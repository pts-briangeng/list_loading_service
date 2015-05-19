import json
import time
import httplib
import copy

from nose.plugins import attrib
from nose import tools
import requests
from liblcp import urls

from tests.integration import base, testing_utilities


@attrib.attr('system_integration')
class ListsServiceIntegrationTest(base.BaseFullIntegrationTestCase):

    @classmethod
    def setUpClass(cls):
        super(ListsServiceIntegrationTest, cls).setUpClass()
        cls.path_params = {
            'base_url': 'http://0.0.0.0:5000',
            'service': 'offers',
            'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'member_id': '34ef0a1f-d5a0-45d7-b065-8ea363875b2f'
        }

    def setUp(self):
        super(ListsServiceIntegrationTest, self).setUp()
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.data = {'filePath': 'test.csv'}

    def test_list_functionality(self):

        def _assert_list_create():
            response = requests.put(base.ListPaths.create(
                **self.__class__.path_params), json.dumps(self.data), headers=self.headers)
            response_content = json.loads(response.content)
            tools.assert_equal(httplib.ACCEPTED, response.status_code)
            tools.assert_in(base.ListPaths.create(
                relative_url=True, **self.__class__.path_params), urls.self_link(response_content))
            time.sleep(2)

        def _assert_search_for_created_list():
            response = requests.get(base.ListPaths.stats(**self.__class__.path_params), headers=self.headers)
            response_content = json.loads(response.content)

            tools.assert_equal(httplib.OK, response.status_code)
            tools.assert_in(base.ListPaths.stats(
                relative_url=True, **self.__class__.path_params), urls.self_link(response_content))
            tools.assert_equal(5, response_content['hits']['total'])

        def _assert_search_for_member_in_list():
            response = requests.get(base.ListPaths.get_list_member(**self.__class__.path_params), headers=self.headers)

            tools.assert_equal(httplib.OK, response.status_code)
            response_content = json.loads(response.content)
            tools.assert_in(base.ListPaths.get_list_member(relative_url=True, **self.__class__.path_params),
                            urls.self_link(response_content))

        def _assert_member_not_found_in_list_return_not_found():
            params = copy.deepcopy(self.__class__.path_params)
            params['member_id'] = "XXXXXXX"
            response = requests.get(base.ListPaths.get_list_member(**params), headers=self.headers)

            tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        def _assert_list_delete():
            response = requests.delete(base.ListPaths.delete(
                **self.__class__.path_params), data=json.dumps({'filePath': '/config/test.csv'}), headers=self.headers)
            response_content = json.loads(response.content)

            tools.assert_equal(httplib.ACCEPTED, response.status_code)
            tools.assert_in(base.ListPaths.create(
                relative_url=True, **self.__class__.path_params), urls.self_link(response_content))
            tools.assert_true(response_content['acknowledged'])
            time.sleep(2)

        def _assert_deleted_list_cannot_be_accessed():
            response = requests.get(base.ListPaths.stats(**self.__class__.path_params), headers=self.headers)
            tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        def _assert_deleted_list_cannot_be_deleted():
            response = requests.delete(base.ListPaths.delete(
                **self.__class__.path_params), data=json.dumps({'filePath': '/config/test.csv'}), headers=self.headers)
            tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        _assert_list_create()
        _assert_search_for_created_list()
        _assert_search_for_member_in_list()
        _assert_member_not_found_in_list_return_not_found()
        _assert_list_delete()
        _assert_deleted_list_cannot_be_accessed()
        _assert_deleted_list_cannot_be_deleted()
