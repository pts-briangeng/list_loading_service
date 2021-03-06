import collections
import httplib
import logging
import os

from elasticsearch import helpers, exceptions

import configuration
from app import exceptions as app_exceptions, operations
from app.services import clients, readers, decorators

import backoff

logger = logging.getLogger(__name__)


class _ElasticSearchDocument(object):

    def __init__(self, action, index, type, account_number):
        self.action = action
        if self.action not in operations.ElasticSearchPermittedOperations.__all__:
            raise ValueError("Incorrect action '{}' specified when executing a Elastic Bulk operation. Permitted "
                             "actions : {}".format(action, operations.ElasticSearchPermittedOperations.__all__))
        self.index = index
        self.type = type
        self.account_number = account_number

    @property
    def doc(self):
        es_document = {
            "_op_type": self.action,
            "_index": self.index,
            "_type": self.type,
            "_id": self.account_number,
            "_source": {
                "accountNumber": self.account_number
            }
        }
        if self.action == operations.ElasticSearchPermittedOperations.DELETE:
            del es_document["_source"]
        return es_document


class ElasticSearchService(object):

    @staticmethod
    @decorators.elastic_search_callback
    @decorators.upload_cleanup
    def create_list(request, stats_only=True):
        logger.info("Creating a new list Params: {}".format(request.unwrap()))
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        file_reader = readers.BulkAccountsFileReaders.get(file_path)

        actions = (
            _ElasticSearchDocument(
                action=request.action, index=request.service, type=request.list_id, account_number=line).doc
            for line in file_reader.get_rows()
        )

        logger.info("Bulk indexing file using index: {}, type: {}".format(request.service, request.list_id))
        elastic_search_client = clients.ElasticSearchClient()

        returned_results = (None, None) if stats_only else ()
        if configuration.data.LIST_PARALLEL_BULK_PROCESSING_ENABLED:
            # Why did we use collections.deque(..)?. helpers.parallel bulk(..) is a generator, meaning it is lazy and
            # won't produce any results until you start consuming them. If you don't care about the results
            # (which by default you don't have to since any error will cause an exception) you can use the consume
            # function from itertools recipes (https://docs.python.org/2/library/itertools.html#recipes)
            # Source
            #   https://discuss.elastic.co/t/helpers-parallel-bulk-in-python-not-working/39498
            collections.deque(
                helpers.parallel_bulk(
                    elastic_search_client, actions, thread_count=configuration.data.BULK_PROCESSING_THREAD_COUNT,
                    chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE, index=request.service,
                    doc_type=request.list_id),
                maxlen=0)
        else:
            returned_results = helpers.bulk(
                elastic_search_client, actions, stats_only=stats_only,
                chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE, index=request.service,
                doc_type=request.list_id)

        success, fail = returned_results if stats_only else (None, len(returned_results), )
        logger.info("Uploading for list '{}'. Stats: Success: {} , Failed: {} .Refreshing index...".format(
            request.list_id, success, fail))
        logger.info("Done! .Refreshing index...")
        elastic_search_client.indices.refresh(index=request.service)
        logger.info("Finished indexing documents")
        file_reader.close()

    @staticmethod
    @decorators.upload_cleanup
    def modify_list_members(request, stats_only=False):
        logger.info("List Modification with action '{}' started...".format(request.action))
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        file_reader = readers.BulkAccountsFileReaders.get(file_path)
        if file_reader.exceeds_allowed_row_count(max_limit_count=configuration.data.ACCOUNTS_UPDATE_MAX_SIZE_ALLOWED):
            raise app_exceptions.TooManyAccountsSpecifiedError()

        actions = []
        members = []

        for line in file_reader.get_rows():
            actions.append(
                _ElasticSearchDocument(
                    action=request.action, index=request.service, type=request.list_id, account_number=line).doc)
            members.append(line)

        logger.info("Bulk indexing file using index: {}, type: {}".format(request.service, request.list_id))
        elastic_search_client = clients.ElasticSearchClient()
        result = helpers.bulk(
            elastic_search_client, actions, stats_only=stats_only,
            chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE, index=request.service, doc_type=request.list_id)
        failed = result[1]
        success = list(set(members).difference(set(failed)))

        file_reader.close()
        logger.info("Modification completed with action '{}' ...Done! Refresh index".format(request.action))
        elastic_search_client.indices.refresh(index=request.service)
        logger.info("Finished indexing documents")

        return {'success': success, 'failed': failed}

    @staticmethod
    @decorators.elastic_search_query_params('query', 'max_tries', 'interval', 'break_on_count')
    def __poll_count(index, doc_type, client, **kwargs):
        query = kwargs.get('query', {"match_all": {}})
        max_tries = kwargs.get('max_tries', 3)
        interval = kwargs.get('interval', 5)
        break_on_count = kwargs.get('break_on_count', 0)

        if break_on_count is None or break_on_count < 0:
            raise app_exceptions.PollCountException("break_on_count value '{}' invalid".format(break_on_count))
        if max_tries < 1:
            raise app_exceptions.PollCountException("max_tries value '{}' invalid".format(max_tries))
        if interval < 0:
            raise app_exceptions.PollCountException("interval value '{}' invalid".format(interval))

        @backoff.on_predicate(
            backoff.constant, lambda count: count != break_on_count, max_tries=max_tries, interval=interval)
        def call_count():
            try:
                result = client.count(index=index, doc_type=doc_type, body={"query": query})
                return result.get("count")
            except exceptions.TransportError as e:
                if e.status_code == httplib.NOT_FOUND:
                    return 0  # If the index was not found, we know the count is 0
                raise

        logger.info("Polling list count...")
        return call_count()

    @staticmethod
    def delete_list(request):
        try:
            logger.info("Elastic Search is deleting /{}/{}".format(request.service, request.list_id))

            client = clients.ElasticSearchClient()
            result = client.delete_by_query(request.service, request.list_id, body={"query": {"match_all": {}}})
            logger.info("Elastic search delete response: {}".format(result))

            count = ElasticSearchService.__poll_count(request.service, request.list_id, client)
            if count:
                raise app_exceptions.PollCountException(
                    "There are '{}' account numbers present in the given index '{}' and type '{}'".format(
                        count, request.service, request.list_id))
        except exceptions.TransportError as e:
            if e.status_code == httplib.NOT_FOUND:
                logger.warning("Elastic search delete request not found")
                raise LookupError
            logger.warning("Elastic search delete request exception: {}".format(e.info))
            raise e

        result["acknowledged"] = True
        return result

    @staticmethod
    def get_list_status(request):
        elastic_search_client = clients.ElasticSearchClient()
        result = elastic_search_client.search(index=request.service, doc_type=request.list_id, search_type="count")
        logger.info("elastic search response {}".format(result))
        if result['hits']['total'] == 0:
            logger.warning("Elastic search (index:{}, Type:{}) not found!".format(request.service, request.list_id))
            raise LookupError
        return result

    @staticmethod
    def get_list_member(request):
        elastic_search_client = clients.ElasticSearchClient()
        if not elastic_search_client.exists(index=request.service, doc_type=request.list_id, id=request.member_id):
            raise LookupError
        return {}
