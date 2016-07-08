import httplib
import json

import requests
from liblcp import urls
from nose import tools
from nose.plugins import attrib

from tests import builders
from tests.integration import base, testing_utilities

PATH_PARAMS = {
    'base_url': 'http://0.0.0.0:5000',
    'service': 'offers',
    'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da'
}


@attrib.attr('local_integration')
class ListStatisticsEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(ListStatisticsEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')

    def test_list_status(self):
        self.queue_stub_response(builders.ESStatusResponseBuilder().http_response())
        response = requests.get(base.ListPaths.stats(**PATH_PARAMS), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_in(base.ListPaths.stats(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))
        tools.assert_equal(1, response_content['hits']['total'])

    def test_list_status_not_found(self):
        self.queue_stub_response(builders.ESStatusResponseBuilder(total_count=0).http_response())
        response = requests.get(base.ListPaths.stats(**PATH_PARAMS), headers=self.headers)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
