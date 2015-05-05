import httplib
import json
import requests
import uuid

from liblcp import context, urls
from nose import tools
from nose.plugins import attrib

from tests.integration import base, testing_utilities


context.set_headers_getter(lambda name: {context.HEADERS_EXTERNAL_BASE_URL: 'http://live.lcpenv',
                                         context.HEADERS_CORRELATION_ID: str(uuid.uuid4()),
                                         context.HEADERS_MODE: 'sandbox',
                                         context.HEADERS_PRINCIPAL: str(uuid.uuid4())}[name])

BASE_SERVICE_URL = 'http://0.0.0.0:5000/'
CREATE_LIST_URL = 'lists/offers/edaa3541-7376-4eb3-8047-aaf78af900da'


@attrib.attr('local_integration')
class CreateListEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(CreateListEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'file': '/test/file'}

    def test_create_list(self):
        response = requests.put(BASE_SERVICE_URL + CREATE_LIST_URL, json.dumps(self.data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(CREATE_LIST_URL, urls.self_link(response_content))

    def test_create_list_with_callback_url(self):
        self.queue_stub_response({"status_code": httplib.OK})
        self.data['callbackUrl'] = 'http://offers-ft.lxc.points.com:1300/'
        response = requests.put(BASE_SERVICE_URL + CREATE_LIST_URL, json.dumps(self.data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(CREATE_LIST_URL, urls.self_link(response_content))

    def test_create_list_missing_file(self):
        data = {'callbackUrl': 'http://offers-ft.lxc.points.com:1300/'}
        response = requests.put(BASE_SERVICE_URL + CREATE_LIST_URL, json.dumps(data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.BAD_REQUEST, response.status_code)
        tools.assert_equal(1, len(response_content['errors']))
        tools.assert_equal('MISSING_FIELD', response_content['errors'][0]['code'])
        tools.assert_equal("'file' is required.", response_content['errors'][0]['description'])
