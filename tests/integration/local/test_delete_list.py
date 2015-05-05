import httplib
import json
import requests
import uuid

from liblcp import context, urls
from nose import tools
from nose.plugins import attrib

from tests.integration import base, testing_utilities
from tests import builders


context.set_headers_getter(lambda name: {context.HEADERS_EXTERNAL_BASE_URL: 'http://live.lcpenv',
                                         context.HEADERS_CORRELATION_ID: str(uuid.uuid4()),
                                         context.HEADERS_MODE: 'sandbox',
                                         context.HEADERS_PRINCIPAL: str(uuid.uuid4())}[name])

BASE_SERVICE_URL = 'http://0.0.0.0:5000/'
DELETE_LIST_URL = 'lists/offers/edaa3541-7376-4eb3-8047-aaf78af900da/'


@attrib.attr('local_integration')
class DeleteListEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(DeleteListEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {}

    def test_delete_list(self):
        self.queue_stub_response(builders.ESDeleteResponseBuilder().with_acknowledged_response().http_response())
        response = requests.delete(BASE_SERVICE_URL + DELETE_LIST_URL, headers=self.headers, data=json.dumps(self.data))
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(DELETE_LIST_URL, urls.self_link(response_content))
        tools.assert_true(response_content['acknowledged'])

    def test_delete_list_with_errors(self):
        self.queue_transport_error()
        response = requests.delete(BASE_SERVICE_URL + DELETE_LIST_URL, headers=self.headers, data=json.dumps(self.data))
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
        tools.assert_equal(len(response_content['errors']), 1)
        tools.assert_equal(response_content['errors'][0]['code'], 'NOT_FOUND')
        tools.assert_equal(response_content['errors'][0]['description'], 'Resource does not exist.')

    def test_delete_list_not_acknowledged(self):
        self.queue_stub_response(builders.ESDeleteResponseBuilder().with_unacknowledged_response().http_response())
        response = requests.delete(BASE_SERVICE_URL + DELETE_LIST_URL, headers=self.headers, data=json.dumps(self.data))
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.INTERNAL_SERVER_ERROR, response.status_code)
        tools.assert_equal(len(response_content['errors']), 1)
        tools.assert_equal(response_content['errors'][0]['code'], 'INTERNAL_SERVER_ERROR')
        tools.assert_equal(response_content['errors'][0]['description'], 'Internal server error.')
