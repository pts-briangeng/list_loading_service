import httplib
import mock

from liblcp import cross_service
from nose.plugins import attrib

from app import models
from app import services
from tests import builders
from tests.integration import base


@attrib.attr('local_integration')
class CreateListServiceTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(CreateListServiceTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.service = services.ElasticSearch()

    @mock.patch.object(cross_service, 'post_or_abort', autospec=True)
    def test_create_list(self, mock_cross_service):
        data = {
            'url': 'url',
            'file': './tests/samples/test.csv',
            'index': 'offers',
            'type': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'callbackUrl': 'http://offers-ft.lxc.points.com:1300/',
        }
        request = models.Request(**data)
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response(builders.ESCreateResponseBuilder().with_items().singleton())
        self.service.create_list(request)
        mock_cross_service.assert_called_once_with(path='http://offers-ft.lxc.points.com:1300/',
                                                   data={'links': {'self': {'href': 'url'}}, 'success': True},
                                                   service='offers')

    @mock.patch.object(cross_service, 'post_or_abort', autospec=True)
    def test_create_list_fails_on_elastic_search_error(self, mock_cross_service):
        data = {
            'url': 'url',
            'file': './tests/samples/test.csv',
            'index': 'offers',
            'type': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'callbackUrl': 'http://offers-ft.lxc.points.com:1300/',
        }
        request = models.Request(**data)
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response(builders.ESCreateResponseBuilder().build().singleton())
        self.service.create_list(request)
        mock_cross_service.assert_called_once_with(path='http://offers-ft.lxc.points.com:1300/',
                                                   data={'links': {'self': {'href': 'url'}}, 'success': False},
                                                   service='offers')

    @mock.patch.object(cross_service, 'post_or_abort', autospec=True)
    def test_create_list_fails_on_non_existant_file(self, mock_cross_service):
        data = {
            'url': 'url',
            'file': 'not_here.csv',
            'index': 'offers',
            'type': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'callbackUrl': 'http://offers-ft.lxc.points.com:1300/',
        }
        request = models.Request(**data)
        self.service.create_list(request)
        mock_cross_service.assert_called_once_with(path='http://offers-ft.lxc.points.com:1300/',
                                                   data={'links': {'self': {'href': 'url'}}, 'success': False},
                                                   service='offers')
