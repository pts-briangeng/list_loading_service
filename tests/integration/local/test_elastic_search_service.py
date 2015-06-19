import httplib
import json
import mock
import os

from liblcp import context
from nose.plugins import attrib
from app.services import elastic

from app import models
from app import services
from tests import builders
from tests.integration import base, testing_utilities


@attrib.attr('local_integration')
class CreateListServiceTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(CreateListServiceTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.test_file = testing_utilities.copy_test_file()
        self.test_path = os.path.join('tests/samples/{}'.format(self.test_file))
        self.service = services.ElasticSearch()

    @mock.patch.object(elastic.requests_wrapper, 'post', autospec=True)
    def test_create_list(self, mock_requests_wrapper_post):
        list_id = 'edaa3541-7376-4eb3-8047-aaf78af900da'
        data = {
            'url': 'url',
            'filePath': self.test_path,
            'service': 'offers',
            'list_id': list_id,
            'callbackUrl': 'http://localhost:5001/offers/callback',
        }
        request = models.Request(**data)
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response(builders.ESCreateResponseBuilder().with_items().singleton())
        # mock put mapping
        self.queue_stub_response({"status_code": httplib.CREATED})
        # mock get index
        self.queue_stub_response({"status_code": httplib.OK})

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
                'file': os.path.join('tests/samples/{}.csv'.format(list_id)),
                'links': {
                    'self': {
                        'href': 'url'
                    },
                    'member': {
                        'href': '/{}/{}/'.format(request.service, request.list_id) + '{member-id}'
                    }
                }
            }))
        testing_utilities.delete_test_files('{}.csv'.format(list_id))

    @mock.patch.object(elastic.requests_wrapper, 'post', autospec=True)
    def test_create_list_fails_on_elastic_search_error(self, mock_requests_wrapper_post):
        list_id = 'edaa3541-7376-4eb3-8047-aaf78af900da'
        data = {
            'url': 'url',
            'filePath': self.test_path,
            'service': 'offers',
            'list_id': list_id,
            'callbackUrl': 'http://localhost:5001/offers/callback',
        }
        request = models.Request(**data)
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response(builders.ESCreateResponseBuilder().build().singleton())
        # mock put mapping
        self.queue_stub_response({"status_code": httplib.CREATED})
        # mock get index
        self.queue_stub_response({"status_code": httplib.OK})

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
                'file': os.path.join('tests/samples/{}.csv'.format(list_id)),
                'links': {
                    'self': {
                        'href': 'url'
                    },
                    'member': {
                        'href': '/{}/{}/'.format(request.service, request.list_id) + '{member-id}'
                    }
                }
            }))
        testing_utilities.delete_test_files('{}.csv'.format(list_id))

    @mock.patch.object(elastic.requests_wrapper, 'post', autospec=True)
    def test_create_list_fails_on_non_existent_file(self, mock_requests_wrapper_post):
        data = {
            'url': 'url',
            'filePath': 'not_here.csv',
            'service': 'offers',
            'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
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
                'file': 'edaa3541-7376-4eb3-8047-aaf78af900da.csv',
                'links': {
                    'self': {
                        'href': 'url'
                    },
                    'member': {
                        'href': '/{}/{}/'.format(request.service, request.list_id) + '{member-id}'
                    }
                }
            }))
        testing_utilities.delete_test_files(self.test_file)
