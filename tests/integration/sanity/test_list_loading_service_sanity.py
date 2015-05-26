import httplib
import urlparse
import json
import requests
import time
import os

from nose.plugins import attrib
from nose import tools

import configuration
from tests.integration import base, testing_utilities

AMOUNT_OF_ACCOUNT_NUMBERS = 9
LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY = 'offers_sanity'
MOCK_VARIATION_ID = 'b8dbaf3f-8a70-49a8-a563-40329e52bb32'
VALID_ACCOUNT_NUMBER = '25b4bff8-4966-4153-8edb-a1d87034b0dc'
TEST_FILE_PATH = 'offers_sanity.csv'
TEST_CALL_BACK_URL = 'http://callback.url'


def create_list():
    create_url = '/lists/{}/{}'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, MOCK_VARIATION_ID)
    post_data = {
        "filePath": TEST_FILE_PATH,
        "callbackUrl": TEST_CALL_BACK_URL
    }

    headers = testing_utilities.generate_headers()
    return requests.put(urlparse.urljoin(configuration.data.list_loading_service_base_url, create_url),
                        data=json.dumps(post_data), headers=headers)


def list_status():
    status_url = '/lists/{}/{}/statistics'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, MOCK_VARIATION_ID)
    headers = testing_utilities.generate_headers()
    return requests.get(urlparse.urljoin(configuration.data.list_loading_service_base_url, status_url), headers=headers)


def delete_list():
    delete_url = '/lists/{}/{}/'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, MOCK_VARIATION_ID)
    headers = testing_utilities.generate_headers()
    post_data = {"filePath": TEST_FILE_PATH}
    return requests.delete(urlparse.urljoin(configuration.data.list_loading_service_base_url, delete_url),
                           data=json.dumps(post_data), headers=headers)


def check_membership(account_number):
    check_membership_url = '/lists/{}/{}/{}'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, MOCK_VARIATION_ID,
                                                    account_number)
    headers = testing_utilities.generate_headers()
    return requests.get(urlparse.urljoin(configuration.data.list_loading_service_base_url, check_membership_url),
                        headers=headers)


def _get_test_file_full_path():
    return os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, TEST_FILE_PATH)


def has_the_upload_file_been_removed():
    return not os.path.isfile(_get_test_file_full_path())


@attrib.attr('sanity_tests')
class SanityTests(base.BaseIntegrationTestCase):

    def test_list_loading_service_succeeds(self):
        response = create_list()
        tools.assert_equal(httplib.ACCEPTED, response.status_code)

        time.sleep(2)

        response = list_status()
        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_equal(AMOUNT_OF_ACCOUNT_NUMBERS, response.json()['hits']['total'])

        response = check_membership(VALID_ACCOUNT_NUMBER)
        tools.assert_equal(httplib.OK, response.status_code)

        response = check_membership(MOCK_VARIATION_ID)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        response = delete_list()
        tools.assert_equal(httplib.ACCEPTED, response.status_code)

        time.sleep(2)

        response = list_status()
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        tools.assert_true(has_the_upload_file_been_removed())
