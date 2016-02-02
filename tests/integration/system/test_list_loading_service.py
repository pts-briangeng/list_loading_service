# -*- coding: UTF-8 -*-

import json
import time
import httplib
import copy
import requests
import urllib

from nose.plugins import attrib
from nose import tools
from liblcp import urls

from tests.integration import base, testing_utilities


@attrib.attr('system_integration')
class ListsServiceIntegrationTest(base.BaseFullIntegrationTestCase):

    @classmethod
    def setUpClass(cls):
        super(ListsServiceIntegrationTest, cls).setUpClass()

    def setUp(self):
        super(ListsServiceIntegrationTest, self).setUp()
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.path_params = {
            'base_url': 'http://0.0.0.0:5000',
            'service': 'offers',
            'list_id': 'list_id',
            'member_id': 'member_id'
        }

    def tearDown(self):
        testing_utilities.delete_test_files(self.renamed_file)

    def _test_list_functionality(self, request_data, path_params, accounts_count):

        def _assert_list_create():
            response = requests.put(base.ListPaths.create(**path_params),
                                    json.dumps(request_data),
                                    headers=self.headers)
            response_content = json.loads(response.content)
            tools.assert_equal(httplib.ACCEPTED, response.status_code)
            tools.assert_in(base.ListPaths.create(
                relative_url=True, **path_params), urls.self_link(response_content))
            time.sleep(2)

        def _assert_search_for_created_list():
            response = requests.get(base.ListPaths.stats(**path_params), headers=self.headers)
            response_content = json.loads(response.content)

            tools.assert_equal(httplib.OK, response.status_code)
            tools.assert_in(base.ListPaths.stats(
                relative_url=True, **path_params), urls.self_link(response_content))
            tools.assert_equal(accounts_count, response_content['hits']['total'])

        def _assert_search_for_member_in_list():
            response = requests.get(base.ListPaths.get_list_member(**path_params), headers=self.headers)

            tools.assert_equal(httplib.OK, response.status_code)
            response_content = json.loads(response.content)
            tools.assert_in(urllib.quote(base.ListPaths.get_list_member(relative_url=True, **path_params)),
                            urls.self_link(response_content).encode('UTF-8'))

        def _assert_member_not_found_in_list_return_not_found():
            params = copy.deepcopy(path_params)
            params['member_id'] = "XXXXXXX"
            response = requests.get(base.ListPaths.get_list_member(**params), headers=self.headers)

            tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        def _assert_list_delete():
            response = requests.delete(base.ListPaths.delete(
                **path_params), data=json.dumps(request_data), headers=self.headers)
            response_content = json.loads(response.content)

            tools.assert_equal(httplib.ACCEPTED, response.status_code)
            tools.assert_in(base.ListPaths.create(
                relative_url=True, **path_params), urls.self_link(response_content))
            tools.assert_true(response_content['acknowledged'])
            time.sleep(2)

        def _assert_deleted_list_cannot_be_accessed():
            response = requests.get(base.ListPaths.stats(**path_params), headers=self.headers)
            tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        def _assert_deleted_list_cannot_be_deleted():
            response = requests.delete(base.ListPaths.delete(
                **path_params), data=json.dumps(request_data), headers=self.headers)
            tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        _assert_list_create()
        _assert_search_for_created_list()
        _assert_search_for_member_in_list()
        _assert_member_not_found_in_list_return_not_found()
        _assert_list_delete()
        _assert_deleted_list_cannot_be_accessed()
        _assert_deleted_list_cannot_be_deleted()

    def test_list_functionality_csv(self):
        self.renamed_file = 'edaa3541-7376-4eb3-8047-aaf78af900da.csv'

        path_params = copy.deepcopy(self.path_params)
        path_params['list_id'] = 'edaa3541-7376-4eb3-8047-aaf78af900da'
        path_params['member_id'] = u'اختبار'.encode('UTF-8')

        request_data = {'filePath': testing_utilities.copy_test_file('accounts_list.csv')}

        self._test_list_functionality(request_data, path_params, 9)

    def test_list_functionality_xlsx(self):
        self.renamed_file = 'c7df9810-90bb-4597-a5ab-c41869bf72e0.xlsx'

        path_params = copy.deepcopy(self.path_params)
        path_params['list_id'] = 'c7df9810-90bb-4597-a5ab-c41869bf72e0'
        path_params['member_id'] = u'آخر النهر'.encode('UTF-8')

        request_data = {'filePath': testing_utilities.copy_test_file('accounts_list.xlsx')}

        self._test_list_functionality(request_data, path_params, 9)
