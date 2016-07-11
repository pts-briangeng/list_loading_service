import logging
import traceback

import elasticsearch
from elasticsearch import exceptions
from elasticsearch.client import query_params

import configuration

logger = logging.getLogger(__name__)


class ElasticSearchClient(elasticsearch.Elasticsearch):

    def __init__(self, **kwargs):
        super(ElasticSearchClient, self).__init__(hosts=[configuration.data.ELASTIC_SEARCH_SERVER], **kwargs)

    def _create_es_index_if_required(self, index):
        try:
            if not self.indices.exists(index=index):
                logger.info("Creating new index {}".format(index))
                self.indices.create(index=index)
        except exceptions.TransportError as e:
            logger.warning("Elastic search get index request exception!")
            logger.warning(traceback.format_exc(), exc_info=1)
            raise e

    def _create_es_mapping(self, index, doc_type):
        try:
            self.indices.put_mapping(
                doc_type=doc_type,
                index=index,
                body={
                    "properties": {
                        "accountNumber": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }
                })
        except exceptions.TransportError as e:
            logger.warning("Elastic search create mapping request exception")
            logger.warning(traceback.format_exc(), exc_info=1)
            raise e

    @query_params('consistency', 'refresh', 'routing', 'replication', 'timeout')
    def bulk(self, body, index=None, doc_type=None, params=None):
        self._create_es_index_if_required(index)
        self._create_es_mapping(index, doc_type)
        return super(ElasticSearchClient, self).bulk(body, index=index, doc_type=doc_type, params=params)
