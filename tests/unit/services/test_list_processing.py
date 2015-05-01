import unittest
import mock

from app import services, models


class TestListProcessing(unittest.TestCase):

    def setUp(self):
        self.service = services.ListProcessing()
        self.request = models.Request(**{
            'url': 'url',
            'index': 'index',
            'type': 'type',
            'file': 'file',
            'callbackUrl': 'callbackUrl'
            })

    @mock.patch.object(services.elasticsearch_service, 'get_list_status', autospec=True)
    def test_list_status(self, mock_elasticsearch_service):
        self.service.get_list_status(self.request)
        mock_elasticsearch_service.assert_called_once_with(self.request)

    @mock.patch.object(services.elasticsearch_service, 'create_list', autospec=True)
    def test_create_list(self, mock_elasticsearch_service):
        self.service.create_list(self.request)
        mock_elasticsearch_service.assert_called_once_with(self.request)

    @mock.patch.object(services.elasticsearch_service, 'delete_list', autospec=True)
    def test_delete_list(self, mock_elasticsearch_service):
        self.service.delete_list(self.request)
        mock_elasticsearch_service.assert_called_once_with(self.request)
