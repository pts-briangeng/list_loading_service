import json
import httplib

from nose.plugins import attrib
from nose import tools
import requests

from tests.integration import base
from tests.integration import testing_utilities


BASE_SERVICE_URL = 'http://0.0.0.0:5000/'
CREATE_LIST_URL = 'index/offers/type/edaa3541-7376-4eb3-8047-aaf78af900da'


@attrib.attr('system_integration')
class ListLoadingServiceIntegrationTest(base.BaseFullIntegrationTestCase):

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'file': '/test/file'}

    def test_create_list(self):
        response = requests.post(BASE_SERVICE_URL + CREATE_LIST_URL, json.dumps(self.data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(CREATE_LIST_URL, response_content['links']['self']['href'])
