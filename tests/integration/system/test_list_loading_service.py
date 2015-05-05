import json
import httplib

from nose.plugins import attrib
from nose import tools
import requests
from liblcp import urls

from tests.integration import base, testing_utilities


BASE_SERVICE_URL = 'http://0.0.0.0:5000/'
BASE_LIST_URL = 'lists/offers/edaa3541-7376-4eb3-8047-aaf78af900da'
LIST_STATUS_URL = 'lists/offers/edaa3541-7376-4eb3-8047-aaf78af900da/statistics'


@attrib.attr('system_integration')
class ListLoadingServiceIntegrationTest(base.BaseFullIntegrationTestCase):

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'file': '/config/test.csv'}  # this file is copied over in the fab task

    def test_create_list(self):

        # Create a list
        response = requests.post(BASE_SERVICE_URL + BASE_LIST_URL, json.dumps(self.data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(BASE_LIST_URL, urls.self_link(response_content))

        # Search for that list
        response = requests.get(BASE_SERVICE_URL + LIST_STATUS_URL, headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(LIST_STATUS_URL, urls.self_link(response_content))
        tools.assert_equal(5, response_content['hits']['total'])

        # Delete the list
        response = requests.delete(BASE_SERVICE_URL + BASE_LIST_URL, data=json.dumps({}), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(BASE_LIST_URL, urls.self_link(response_content))
        tools.assert_true(response_content['acknowledged'])

        # Ensure the list was deleted by searching for it and trying to delete it again
        response = requests.get(BASE_SERVICE_URL + LIST_STATUS_URL, headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(LIST_STATUS_URL, urls.self_link(response_content))
        tools.assert_equal(0, response_content['hits']['total'])

        response = requests.delete(BASE_SERVICE_URL + BASE_LIST_URL, data=json.dumps({}), headers=self.headers)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
