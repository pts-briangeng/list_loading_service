import json
import time
import httplib

from nose.plugins import attrib
from nose import tools
import requests
from liblcp import urls

from tests.integration import base, testing_utilities


PATH_PARAMS = {
    'base_url': 'http://0.0.0.0:5000',
    'service': 'offers',
    'id': 'edaa3541-7376-4eb3-8047-aaf78af900da'
}


@attrib.attr('system_integration')
class ListLoadingServiceIntegrationTest(base.BaseFullIntegrationTestCase):

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'file': '/config/test.csv'}  # this file is copied over in the fab task

    def test_create_list(self):

        # Create a list
        response = requests.put(base.ListPaths.create(**PATH_PARAMS), json.dumps(self.data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(base.ListPaths.create(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))

        time.sleep(2)
        # Search for that list
        response = requests.get(base.ListPaths.stats(**PATH_PARAMS), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(base.ListPaths.stats(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))
        tools.assert_equal(5, response_content['hits']['total'])

        # Delete the list
        response = requests.delete(base.ListPaths.delete(PATH_PARAMS), data=json.dumps({}), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(base.ListPaths.create(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))
        tools.assert_true(response_content['acknowledged'])

        time.sleep(2)
        # Ensure the list was deleted by searching for it and trying to delete it again
        response = requests.get(base.ListPaths.stats(**PATH_PARAMS), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(base.ListPaths.stats(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))
        tools.assert_equal(0, response_content['hits']['total'])

        response = requests.delete(base.ListPaths.delete(PATH_PARAMS), data=json.dumps({}), headers=self.headers)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
