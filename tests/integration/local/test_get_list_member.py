import httplib
import json

import requests
from liblcp import urls
from nose import tools
from nose.plugins import attrib

from tests.integration import base, testing_utilities

PATH_PARAMS = {
    'base_url': 'http://localhost:5000',
    'service': 'offers',
    'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
    'member_id': '34ef0a1f-d5a0-45d7-b065-8ea363875b2f'
}


@attrib.attr('local_integration')
class GetListMemberEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(GetListMemberEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')

    def test_get_member(self):
        self.queue_stub_response({"status_code": httplib.OK})
        response = requests.get(base.ListPaths.get_list_member(**PATH_PARAMS), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(base.ListPaths.get_list_member(**PATH_PARAMS), urls.self_link(response_content))

    def test_get_member_not_found(self):
        self.queue_stub_response({"status_code": httplib.NOT_FOUND})
        response = requests.get(base.ListPaths.get_list_member(**PATH_PARAMS), headers=self.headers)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
