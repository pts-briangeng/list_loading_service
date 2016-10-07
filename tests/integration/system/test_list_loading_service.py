# -*- coding: UTF-8 -*-

import copy
import uuid

from nose.plugins import attrib

from tests.integration import base, testing_utilities
from tests.integration.system import asserts

import json
import httplib
import requests
from nose import tools


@attrib.attr('system_integration')
class ListsServiceIntegrationTest(base.BaseFullIntegrationTestCase):

    @classmethod
    def setUpClass(cls):
        super(ListsServiceIntegrationTest, cls).setUpClass()

    def setUp(self):
        super(ListsServiceIntegrationTest, self).setUp()
        self.headers = testing_utilities.generate_headers(base_url='http://live.lcpenv')
        self.test_files = []
        self.path_params = {
            'base_url': 'http://0.0.0.0:5000',
            'service': 'offers',
            'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'member_id': 'dff85334-2af5-492c-827d-efb7c98b2917'
        }

    def tearDown(self):
        for test_file in self.test_files:
            testing_utilities.delete_test_files(test_file)

    def test_normal_csv(self):
        path_params = copy.deepcopy(self.path_params)
        path_params['member_id'] = u'اختبار'.encode('UTF-8')

        request_data = {'filePath': self._get_test_file('normal.csv')}

        asserts.assert_list_functionality(request_data, path_params, 9, self.headers)

    def test_dos_csv(self):
        request_data = {'filePath': self._get_test_file('dos.csv')}
        asserts.assert_list_functionality(request_data, self.path_params, 9, self.headers)

    def test_mac_csv(self):
        request_data = {'filePath': self._get_test_file('mac.csv')}
        asserts.assert_list_functionality(request_data, self.path_params, 9, self.headers)

    def test_windows_csv(self):
        request_data = {'filePath': self._get_test_file('windows.csv')}
        asserts.assert_list_functionality(request_data, self.path_params, 9, self.headers)

    def test_append_to_list(self):
        asserts.assert_append_to_list({'filePath': self._get_test_file('normal.csv')}, self.path_params, self.headers)

    def test_delete_from_list(self):
        path_params = copy.deepcopy(self.path_params)
        path_params['member_id'] = u'اختبار'.encode('UTF-8')

        request_data = {'filePath': self._get_test_file('normal.csv')}
        asserts.assert_list_create(request_data, path_params, self.headers)
        asserts.assert_search_for_created_list(path_params, 9, self.headers)

        asserts.assert_delete_from_list(
            {'filePath': self._get_test_file('normal_delete.csv')}, path_params, self.headers)
        asserts.assert_member_not_found_in_list(path_params, self.headers, member_id=path_params['member_id'])

    def test_load(self):
        list_requests = []
        self.renamed_files = []
        for _ in xrange(10):
            file_id = str(uuid.uuid4())
            path_params = copy.deepcopy(self.path_params)
            path_params['list_id'] = file_id
            self.renamed_files.append('{}.csv'.format(file_id))
            request_data = {'filePath': self._get_test_file('normal_large.csv')}
            list_requests.append((request_data, path_params, 50000))
            asserts.assert_list_create(request_data, path_params, self.headers)

        for list_request in list_requests:
            asserts.assert_list_functionality(*list_request, headers=self.headers, assert_create=False)

    def test_list_functionality_xlsx(self):
        self.renamed_files = ['c7df9810-90bb-4597-a5ab-c41869bf72e0.xlsx']

        path_params = copy.deepcopy(self.path_params)
        path_params['list_id'] = 'c7df9810-90bb-4597-a5ab-c41869bf72e0'
        path_params['member_id'] = u'آخر النهر'.encode('UTF-8')

        request_data = {'filePath': self._get_test_file('accounts_list.xlsx')}

        asserts.assert_list_functionality(request_data, path_params, 9, self.headers)
        
    def test_delete_list_index_does_not_exist(self):
        path_params = {
            'base_url': 'http://0.0.0.0:5000',
            'service': 'nonexistentindex',
            'list_id': 'edaa3541-7376-4eb3-8047-aaf78af900da',
            'member_id': 'dff85334-2af5-492c-827d-efb7c98b2917'
        }

        response = requests.delete(base.ListPaths.delete(**path_params), data=json.dumps({}), headers=self.headers)

        tools.assert_equal(httplib.NOT_FOUND, response.status_code)

    def _get_test_file(self, file_type):
        self.test_files.append(testing_utilities.copy_test_file(file_type))
        return self.test_files[-1]
