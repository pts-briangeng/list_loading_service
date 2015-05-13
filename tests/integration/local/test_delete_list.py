import httplib
import json

import requests
from liblcp import urls
from nose import tools
from nose.plugins import attrib

from tests.integration import base, testing_utilities
from tests import builders


PATH_PARAMS = {
    'base_url': 'http://0.0.0.0:5000',
    'service': 'offers',
    'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da'
}


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
        response = requests.delete(base.ListPaths.delete(**PATH_PARAMS),
                                   headers=self.headers,
                                   data=json.dumps(self.data))
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(base.ListPaths.delete(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))
        tools.assert_true(response_content['acknowledged'])

    def test_delete_list_with_errors(self):
        self.queue_transport_error()
        response = requests.delete(base.ListPaths.delete(**PATH_PARAMS),
                                   headers=self.headers,
                                   data=json.dumps(self.data))
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
        tools.assert_equal(len(response_content['errors']), 1)
        tools.assert_equal(response_content['errors'][0]['code'], 'NOT_FOUND')
        tools.assert_equal(response_content['errors'][0]['description'], 'Resource does not exist.')
