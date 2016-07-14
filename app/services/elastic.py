import httplib
import logging
import os
import shutil

import collections
from elasticsearch import helpers, exceptions

import configuration
from app.services import clients, readers, decorators

logger = logging.getLogger(__name__)


class _ElasticSearchDocument(object):

    def __init__(self, index, type, account_number):
        self.index = index
        self.type = type
        self.account_number = account_number

    @property
    def doc(self):
        return {
            "_index": self.index,
            "_type": self.type,
            "_id": self.account_number,
            "_source": {
                "accountNumber": self.account_number
            }
        }


class ElasticSearchService(object):

    @staticmethod
    @decorators.elastic_search_callback
    def create_list(request):
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        if not os.path.isfile(file_path):
            raise IOError("File {} does not exist!".format(file_path))

        updated_path = decorators.rename_file(file_path, request.list_id)
        shutil.move(file_path, updated_path)

        file_reader = readers.BulkAccountsFileReaders.get(updated_path)
        if file_reader.is_empty():
            raise EOFError("File {} is empty!".format(file_path))

        actions = (
            _ElasticSearchDocument(
                index=request.service, type=request.list_id, account_number=line).doc
            for line in file_reader.get_rows()
        )

        logger.info("Bulk indexing file using index: {}, type: {}".format(request.service, request.list_id))
        elastic_search_client = clients.ElasticSearchClient()

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
            helpers.bulk(
                elastic_search_client, actions, chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE,
                index=request.service, doc_type=request.list_id)

        logger.info("Uploading ...Done! Refresh index")
        elastic_search_client.indices.refresh(index=request.service)
        logger.info("Finished indexing documents")
        file_reader.close()
        return updated_path

    @staticmethod
    def delete_list(request):
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        try:
            logger.info("Elasticsearch is deleting index: {}, doc_type: {}".format(request.service, request.list_id))
            elastic_search_client = clients.ElasticSearchClient()
            result = elastic_search_client.indices.delete_mapping(index=request.service, doc_type=request.list_id)
            logger.info("Elastic search delete response {}".format(result))
        except exceptions.TransportError as e:
            if e.status_code == httplib.NOT_FOUND:
                logger.warning("Elastic search delete request not found")
                raise LookupError
            else:
                logger.warning("Elastic search delete request exception: {}".format(e.info))
                raise e

        if not result.get('acknowledged', False):
            logger.warning("Elastic search delete response not acknowledged successfully")
            raise Exception

        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning("Error deleting file: {}".format(e))

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
