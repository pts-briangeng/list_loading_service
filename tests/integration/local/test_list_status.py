import httplib
import json

import requests
from liblcp import urls
from nose import tools
from nose.plugins import attrib

from tests.integration import base, testing_utilities
from tests import builders


BASE_SERVICE_URL = 'http://0.0.0.0:5000/'
LIST_STATUS_URL = 'lists/offers/edaa3541-7376-4eb3-8047-aaf78af900da/statistics'


@attrib.attr('local_integration')
class ListCountEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(ListCountEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')

    def test_list_status(self):
        self.queue_stub_response(builders.ESStatusResponseBuilder().http_response())
        response = requests.get(BASE_SERVICE_URL + LIST_STATUS_URL, headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(LIST_STATUS_URL, urls.self_link(response_content))
        tools.assert_equal(1, response_content['hits']['total'])

    def test_list_status_not_found(self):
        self.queue_stub_response(builders.ESStatusResponseBuilder(total_count=0).http_response())
        response = requests.get(BASE_SERVICE_URL + LIST_STATUS_URL, headers=self.headers)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
