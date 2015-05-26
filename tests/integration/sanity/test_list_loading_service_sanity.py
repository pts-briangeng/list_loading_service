import httplib
import urlparse
import json
import requests
import time
import os
import uuid
import random

from retrying import retry

from nose.plugins import attrib
from nose import tools

import configuration
from tests.integration import base, testing_utilities

LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY = 'offers'
TEST_FILE_PATH = 'offers_sanity.csv'
MOCK_VARIATION_ID = str(uuid.uuid4())


def create_list():
    create_url = '/lists/{}/{}'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, MOCK_VARIATION_ID)
    post_data = {
        "filePath": TEST_FILE_PATH,
        "callbackUrl": ""
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
    return os.path.join(configuration.data.volume_mappings_file_upload_target, TEST_FILE_PATH)


def _has_the_upload_file_been_removed():
    return not os.path.isfile(_get_test_file_full_path())


def _get_testing_data():
    with open(_get_test_file_full_path()) as f:
        account_numbers = f.readlines()
    return len(account_numbers), random.choice(account_numbers)


def _retry_if_assertion_error(exception):
    return isinstance(exception, AssertionError)


@attrib.attr('sanity_tests')
class SanityTests(base.BaseIntegrationTestCase):

    def test_list_loading_service_succeeds(self):
        amount_of_account_numbers, valid_account_number = _get_testing_data()

        response = create_list()
        tools.assert_equal(httplib.ACCEPTED, response.status_code)

        time.sleep(2)

        response = list_status()
        tools.assert_equal(httplib.OK, response.status_code)
        tools.assert_equal(amount_of_account_numbers, response.json()['hits']['total'])

        response = check_membership(valid_account_number)
        tools.assert_equal(httplib.OK, response.status_code)

        response = check_membership(MOCK_VARIATION_ID)
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        response = delete_list()
        tools.assert_equal(httplib.ACCEPTED, response.status_code)

        time.sleep(2)

        response = list_status()
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)

        tools.assert_true(_has_the_upload_file_been_removed())

    @retry(stop_max_attempt_number=3, wait_fixed=1000, retry_on_exception=_retry_if_assertion_error)
    def tearDown(self):
        response = list_status()
        tools.assert_equal(httplib.NOT_FOUND, response.status_code)
