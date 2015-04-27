import unittest
import os

import mock
import liblcp
from elasticsearch import helpers
import elasticsearch

from app import models
from app.services import list_processing


class TestListProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('file.csv', 'w') as test_file:
            test_file.write('abc')

    @classmethod
    def tearDownClass(cls):
        os.remove('file.csv')

    def setUp(self):
        self.service = list_processing.ListProcessingService()
        self.data = {
            'url': 'url',
            'file': 'file.csv',
            'index': 'index',
            'type': 'type',
            'callbackUrl': 'callback',
        }

    @mock.patch.object(liblcp.cross_service, 'post', autospec=True)
    @mock.patch.object(helpers, 'bulk')
    @mock.patch.object(elasticsearch, "Elasticsearch")
    def test_elastic_search_operation(self, mock_elastic_search, mock_bulk, mock_cross_service_post):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_cross_service_post.return_value = True
        request = models.Request(**self.data)
        self.service.create_list(request)

        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     [{'_type': 'type', '_id': 1L, '_source': {'id': 'abc'}, '_index': 'index'}])
        mock_elastic_search.return_value.indices.refresh.assert_called_with(index='index')
        mock_cross_service_post.assert_has_calls([mock.call(path='callback',
                                                            data={'links': {'self': {'href': 'url'}}, 'success': True},
                                                            service='index')])

    @mock.patch.object(liblcp.cross_service, 'post', autospec=True)
    def test_elastic_search_operation_without_callback(self, mock_cross_service_post):
        self.data.pop('callbackUrl')
        mock_cross_service_post.return_value = True
        request = models.Request(**self.data)
        self.service.create_list(request)
        mock_cross_service_post.assert_has_calls([])
