import httplib
import os
import unittest

import mock
from elasticsearch import exceptions
from nose import tools

import configuration
from app.services import clients

INTERNAL_SERVER_ERROR_EXCEPTION = exceptions.TransportError(httplib.INTERNAL_SERVER_ERROR,
                                                            'Internal Server error',
                                                            {
                                                                'status': httplib.INTERNAL_SERVER_ERROR,
                                                                'error': 'Server error'
                                                            })


class TestElasticSearchClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))

    def setUp(self):
        self.client = clients.ElasticSearchClient()

    @tools.raises(exceptions.TransportError)
    @mock.patch.object(clients.elasticsearch.client, 'Elasticsearch', autospec=True)
    def test_raises_exception_when_creating_index(self, mock_elastic_search):
        self.client.indices = mock.MagicMock()
        self.client.indices.create.side_effect = INTERNAL_SERVER_ERROR_EXCEPTION

        self.client.bulk([{'_type': 'id', '_id': 'abc', '_source': {'accountNumber': 'abc'}, '_index': 'service'}],
                         index='service',
                         doc_type='id')

        tools.assert_equal(0, self.client.indices.put_mapping.call_count)
        tools.assert_equal(0, self.client.indices.refresh.call_count)
        tools.assert_equal(0, self.client.bulk.call_count)

    @tools.raises(exceptions.TransportError)
    @mock.patch.object(clients.elasticsearch.client, 'Elasticsearch', autospec=True)
    def test_raises_exception_when_mapping_put_raises_exception(self, mock_elastic_search):
        self.client.indices = mock.MagicMock()
        self.client.indices.exists.side_effect = INTERNAL_SERVER_ERROR_EXCEPTION

        self.client.bulk([{'_type': 'id', '_id': 'abc', '_source': {'accountNumber': 'abc'}, '_index': 'service'}],
                         index='service',
                         doc_type='id')

        self.client.indices.exists.assert_called_with_once(index='service')
        tools.assert_equal(0, self.client.indices.create.call_count)
        tools.assert_equal(0, self.client.indices.refresh.call_count)
        tools.assert_equal(0, self.client.indices.put_mapping.call_count)

    @tools.raises(exceptions.TransportError)
    @mock.patch.object(clients.elasticsearch.client, 'Elasticsearch', autospec=True)
    def test_raises_exception_when_mapping_put(self, mock_elastic_search):
        self.client.indices = mock.MagicMock()
        self.client.indices.exists.return_value = True
        self.client.indices.put_mapping.side_effect = INTERNAL_SERVER_ERROR_EXCEPTION

        self.client.bulk([{'_type': 'id', '_id': 'abc', '_source': {'accountNumber': 'abc'}, '_index': 'service'}],
                         index='service',
                         doc_type='id')

        self.client.indices.exists.assert_called_with_once(index='service')
        tools.assert_equal(1, self.client.indices.create.call_count)
        tools.assert_equal(1, self.client.indices.refresh.call_count)
        self.client.indices.put_mapping.assert_called_once_with(
            index='service',
            doc_type='id',
            body={
                "properties": {
                    "accountNumber": {
                        "type": "string",
                        "index": "not_analyzed"
                    }
                }
            })

    @mock.patch.object(clients.elasticsearch.client.Elasticsearch, 'bulk', autospec=True)
    def test_create_index_and_mapping_success(self, mock_elastic_search_bulk_method):
        self.client.indices = mock.MagicMock()
        self.client.indices.exists.return_value = False

        self.client.bulk([{'_type': 'id', '_id': 'abc', '_source': {'accountNumber': 'abc'}, '_index': 'service'}],
                         index='service',
                         doc_type='id')

        self.client.indices.exists.assert_called_once_with(index='service')
        self.client.indices.create.assert_called_once_with(index='service')
        self.client.indices.put_mapping.assert_called_once_with(index='service',
                                                                doc_type='id',
                                                                body={
                                                                    "properties": {
                                                                        "accountNumber": {
                                                                            "type": "string",
                                                                            "index": "not_analyzed"
                                                                        }
                                                                    }
                                                                })
        mock_elastic_search_bulk_method.assert_called_once_with(
            self.client,
            [{'_type': 'id', '_id': 'abc', '_source': {'accountNumber': 'abc'}, '_index': 'service'}],
            index='service',
            params={},
            doc_type='id'
        )
