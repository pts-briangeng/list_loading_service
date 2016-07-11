import logging
import traceback

import elasticsearch
from elasticsearch import exceptions, connection, connection_pool, serializer, transport, client

import configuration

logger = logging.getLogger(__name__)


class Transport(elasticsearch.Transport):

    def __init__(self, hosts, connection_class=connection.Urllib3HttpConnection,
                 connection_pool_class=connection_pool.ConnectionPool, host_info_callback=transport.get_host_info,
                 sniff_on_start=False, sniffer_timeout=None, sniff_timeout=.1,
                 sniff_on_connection_fail=False, serializer=serializer.JSONSerializer(), serializers=None,
                 default_mimetype='application/json', max_retries=1, retry_on_status=(503, 504,),
                 retry_on_timeout=False, send_get_body_as='GET', **kwargs):

        super(Transport, self).__init__(
            hosts, connection_class=connection_class, connection_pool_class=connection_pool_class,
            host_info_callback=host_info_callback, sniff_on_start=sniff_on_start, sniffer_timeout=sniffer_timeout,
            sniff_timeout=sniff_timeout, sniff_on_connection_fail=sniff_on_connection_fail, serializer=serializer,
            serializers=serializers, default_mimetype=default_mimetype, max_retries=max_retries,
            retry_on_status=retry_on_status, retry_on_timeout=retry_on_timeout,
            send_get_body_as=send_get_body_as, **kwargs)


class ElasticSearchClient(elasticsearch.Elasticsearch):

    def __init__(self, **kwargs):
        super(ElasticSearchClient, self).__init__(
            hosts=[configuration.data.ELASTIC_SEARCH_SERVER], transport_class=Transport, **kwargs)

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

    @client.query_params('consistency', 'refresh', 'routing', 'replication', 'timeout')
    def bulk(self, body, index=None, doc_type=None, params=None):
        self._create_es_index_if_required(index)
        self._create_es_mapping(index, doc_type)
        return super(ElasticSearchClient, self).bulk(body, index=index, doc_type=doc_type, params=params)
