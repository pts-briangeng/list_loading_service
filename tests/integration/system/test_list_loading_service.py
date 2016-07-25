# -*- coding: UTF-8 -*-

import uuid
import json
import time
import backoff
import httplib
import copy
import urllib

import requests
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
        self.renamed_files = ['edaa3541-7376-4eb3-8047-aaf78af900da.csv']
        self.path_params = {
            'base_url': 'http://0.0.0.0:5000',
            'service': 'offers',
            'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'member_id': 'dff85334-2af5-492c-827d-efb7c98b2917'
        }

    def tearDown(self):
        for renamed_file in self.renamed_files:
            testing_utilities.delete_test_files(renamed_file)

    def _assert_list_create(self, request_data, path_params):
        response = requests.put(base.ListPaths.create(**path_params),
                                json.dumps(request_data),
                                headers=self.headers)
        response_content = json.loads(response.content)
        tools.assert_equal(httplib.ACCEPTED, response.status_code)
        tools.assert_in(base.ListPaths.create(relative_url=True, **path_params), urls.self_link(response_content))

    @backoff.on_exception(backoff.expo, AssertionError, max_tries=10)
    def _test_list_functionality(self, request_data, path_params, accounts_count, assert_create=True):

        @backoff.on_exception(backoff.expo, AssertionError, max_tries=10)
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

        if assert_create:
            self._assert_list_create(request_data, path_params)

        _assert_search_for_created_list()
        _assert_search_for_member_in_list()
        _assert_member_not_found_in_list_return_not_found()
        _assert_list_delete()
        _assert_deleted_list_cannot_be_accessed()
        _assert_deleted_list_cannot_be_deleted()

    def test_normal_csv(self):
        path_params = copy.deepcopy(self.path_params)
        path_params['member_id'] = u'اختبار'.encode('UTF-8')

        request_data = {'filePath': testing_utilities.copy_test_file('normal.csv')}

        self._test_list_functionality(request_data, path_params, 9)

    def test_dos_csv(self):
        request_data = {'filePath': testing_utilities.copy_test_file('dos.csv')}
        self._test_list_functionality(request_data, self.path_params, 9)

    def test_mac_csv(self):
        request_data = {'filePath': testing_utilities.copy_test_file('mac.csv')}
        self._test_list_functionality(request_data, self.path_params, 9)

    def test_windows_csv(self):
        request_data = {'filePath': testing_utilities.copy_test_file('windows.csv')}
        self._test_list_functionality(request_data, self.path_params, 9)

    def test_list_functionality_xlsx(self):
        self.renamed_files = ['c7df9810-90bb-4597-a5ab-c41869bf72e0.xlsx']

        path_params = copy.deepcopy(self.path_params)
        path_params['list_id'] = 'c7df9810-90bb-4597-a5ab-c41869bf72e0'
        path_params['member_id'] = u'آخر النهر'.encode('UTF-8')

        request_data = {'filePath': testing_utilities.copy_test_file('accounts_list.xlsx')}

        self._test_list_functionality(request_data, path_params, 9)

    def test_load(self):
        list_requests = []
        self.renamed_files = []
        for _ in xrange(10):
            file_id = str(uuid.uuid4())
            path_params = copy.deepcopy(self.path_params)
            path_params['list_id'] = file_id
            self.renamed_files.append('{}.csv'.format(file_id))
            request_data = {'filePath': testing_utilities.copy_test_file('normal_large.csv')}
            list_requests.append((request_data, path_params, 50000))
            self._assert_list_create(request_data, path_params)

        for list_request in list_requests:
            self._test_list_functionality(*list_request, assert_create=False)
