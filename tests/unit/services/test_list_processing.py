import unittest
import mock

import liblcp

from app import models
from app.services import list_processing


class TestListProcessing(unittest.TestCase):

    def setUp(self):
        self.service = list_processing.ListProcessingService()
        self.data = {
            'url': 'url',
            'file': 'file',
            'index': 'index',
            'type': 'type',
            'callbackUrl': 'callback',
        }

    @mock.patch.object(liblcp.cross_service, 'post', autospec=True)
    def test_elastic_search_operation(self, mock_cross_service_post):
        mock_cross_service_post.return_value = True
        request = models.Request(**self.data)
        self.service._elastic_search_operation(request)
        mock_cross_service_post.assert_has_calls([mock.call(path='callback',
                                                            data={'links': {'self': {'href': 'url'}}, 'success': True},
                                                            service='index')])

    @mock.patch.object(liblcp.cross_service, 'post', autospec=True)
    def test_elastic_search_operation_without_callback(self, mock_cross_service_post):
        self.data.pop('callbackUrl')
        mock_cross_service_post.return_value = True
        request = models.Request(**self.data)
        self.service._elastic_search_operation(request)
        mock_cross_service_post.assert_has_calls([])
