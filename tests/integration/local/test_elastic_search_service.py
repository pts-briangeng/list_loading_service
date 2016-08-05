import httplib
import json
import os

import mock
from liblcp import context
from nose.plugins import attrib

from app import models
from app import services
from app.services import readers, decorators
from tests import builders
from tests.integration import base, testing_utilities
from tests.mocks import generator


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

    def tearDown(self):
        testing_utilities.delete_test_files(self.test_file)

    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    def test_create_list(self, mock_requests_wrapper_post, mock_file_readers):

        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        mock_csv_reader.get_rows.return_value = generator("account_no")
        mock_file_readers.get.return_value = mock_csv_reader
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
                'links': {
                    'self': {
                        'href': 'url'
                    },
                    'member': {
                        'href': '/{}/{}/{{member-id}}'.format(request.service, request.list_id)
                    }
                }
            }))

    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    def test_create_list_fails_on_elastic_search_error(self, mock_requests_wrapper_post, mock_file_readers):
        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        mock_csv_reader.get_rows.return_value = generator("account_no")

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
                'links': {
                    'self': {
                        'href': 'url'
                    }
                }
            }))

    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
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
                'links': {
                    'self': {
                        'href': 'url'
                    }
                }
            }))
