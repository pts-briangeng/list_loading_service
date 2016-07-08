import httplib
import json
import os

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
class CreateListEndpointTest(base.BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls, **kwargs):
        super(CreateListEndpointTest, cls).setUpClass(**kwargs)
        base.BaseIntegrationTestCase.setUpClass()

    def setUp(self):
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'filePath': '/test/file'}

    def test_create_list(self):
        test_file = testing_utilities.copy_test_file()
        response = requests.put(
            base.ListPaths.create(**PATH_PARAMS),
            json.dumps({'filePath': os.path.join(os.getcwd(), "tests/samples/{}".format(test_file))}),
            headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(base.ListPaths.create(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))

    def test_create_list_with_callback_url(self):
        self.queue_stub_response({"status_code": httplib.OK})

        self.data['callbackUrl'] = 'http://localhost:5001/offers/callback'
        response = requests.put(base.ListPaths.create(**PATH_PARAMS), json.dumps(self.data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(base.ListPaths.create(relative_url=True, **PATH_PARAMS), urls.self_link(response_content))

    def test_create_list_missing_file(self):
        data = {'callbackUrl': 'http://localhost:5001/offers/callback'}
        response = requests.put(base.ListPaths.create(**PATH_PARAMS), json.dumps(data), headers=self.headers)
        response_content = json.loads(response.content)

        tools.assert_equal(httplib.BAD_REQUEST, response.status_code)
        tools.assert_equal(1, len(response_content['errors']))
        tools.assert_equal('MISSING_FIELD', response_content['errors'][0]['code'])
        tools.assert_equal("'filePath' is required.", response_content['errors'][0]['description'])
