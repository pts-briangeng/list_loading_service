import httplib
import json
import mock

from liblcp import context
from nose.plugins import attrib
from app.services import elasticsearch_service

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

    @mock.patch.object(elasticsearch_service.requests_wrapper, 'post', autospec=True)
    def test_create_list(self, mock_requests_wrapper_post):
        data = {
            'url': 'url',
            'file': './tests/samples/test.csv',
            'service': 'offers',
            'id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'callbackUrl': 'http://localhost:5001/offers/callback',
        }
        request = models.Request(**data)
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response(builders.ESCreateResponseBuilder().with_items().singleton())

        self.service.create_list(request)

        mock_requests_wrapper_post.assert_called_once_with(
            url='http://localhost:5001/offers/callback',
            headers={
                'PTS-LCP-Base-URL': context.get_header_value(context.HEADERS_EXTERNAL_BASE_URL),
                'PTS-LCP-Mode': context.get_header_value(context.HEADERS_MODE),
                'PTS-LCP-CID': context.get_header_value(context.HEADERS_CORRELATION_ID),
                'PTS-LCP-Principal': context.get_header_value(context.HEADERS_PRINCIPAL),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'success': True,
                'links': {
                    'self': {
                        'href': 'url'
                    }
                }
            }))

    @mock.patch.object(elasticsearch_service.requests_wrapper, 'post', autospec=True)
    def test_create_list_fails_on_elastic_search_error(self, mock_requests_wrapper_post):
        data = {
            'url': 'url',
            'file': './tests/samples/test.csv',
            'service': 'offers',
            'id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'callbackUrl': 'http://localhost:5001/offers/callback',
        }
        request = models.Request(**data)
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response(builders.ESCreateResponseBuilder().build().singleton())

        self.service.create_list(request)

        mock_requests_wrapper_post.assert_called_once_with(
            url='http://localhost:5001/offers/callback',
            headers={
                'PTS-LCP-Base-URL': context.get_header_value(context.HEADERS_EXTERNAL_BASE_URL),
                'PTS-LCP-Mode': context.get_header_value(context.HEADERS_MODE),
                'PTS-LCP-CID': context.get_header_value(context.HEADERS_CORRELATION_ID),
                'PTS-LCP-Principal': context.get_header_value(context.HEADERS_PRINCIPAL),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'success': False,
                'links': {
                    'self': {
                        'href': 'url'
                    }
                }
            }))

    @mock.patch.object(elasticsearch_service.requests_wrapper, 'post', autospec=True)
    def test_create_list_fails_on_non_existant_file(self, mock_requests_wrapper_post):
        data = {
            'url': 'url',
            'file': 'not_here.csv',
            'service': 'offers',
            'id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'callbackUrl': 'http://localhost:5001/offers/callback',
        }
        request = models.Request(**data)

        self.service.create_list(request)

        mock_requests_wrapper_post.assert_called_once_with(
            url='http://localhost:5001/offers/callback',
            headers={
                'PTS-LCP-Base-URL': context.get_header_value(context.HEADERS_EXTERNAL_BASE_URL),
                'PTS-LCP-Mode': context.get_header_value(context.HEADERS_MODE),
                'PTS-LCP-CID': context.get_header_value(context.HEADERS_CORRELATION_ID),
                'PTS-LCP-Principal': context.get_header_value(context.HEADERS_PRINCIPAL),
                'Content-Type': 'application/json'
            },
            data=json.dumps({
                'success': False,
                'links': {
                    'self': {
                        'href': 'url'
                    }
                }
            }))
