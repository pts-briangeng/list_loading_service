import httplib
import json
import os
import unittest

import requests
from liblcp import urls
from nose import tools
from nose.plugins import attrib

from tests.integration import base, testing_utilities

PATH_PARAMS = {
    'base_url': 'http://0.0.0.0:5000',
    'service': 'offers',
    'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da'
}


@attrib.attr('local_integration')
class AppendListEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(AppendListEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.test_file = testing_utilities.copy_test_file()
        self.test_path = os.path.join('tests/samples/{}'.format(self.test_file))
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'filePath': self.test_path}

    def tearDown(self):
        testing_utilities.delete_test_files(self.test_file)

    @unittest.skip("BG: will be fixed soon")
    def test_append_list(self):
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response({"status_code": httplib.OK})
        self.queue_stub_response({"status_code": httplib.OK})

        response = requests.put(
            base.ListPaths.append(**PATH_PARAMS),
            json.dumps(self.data),
            headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(base.ListPaths.append(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))

    def test_append_list_missing_file(self):
        data = {}
        response = requests.put(base.ListPaths.append(**PATH_PARAMS), json.dumps(data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.BAD_REQUEST, response.status_code)
        tools.assert_equal(1, len(response_content['errors']))
        tools.assert_equal('MISSING_FIELD', response_content['errors'][0]['code'])
        tools.assert_equal("'filePath' is required.", response_content['errors'][0]['description'])
