# -*- coding: UTF-8 -*-

import httplib
import json
import random
import urlparse
import uuid

import backoff
import requests
from nose import tools
from nose.plugins import attrib

import configuration
from tests.integration import base, testing_utilities

LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY = 'offers'
TEST_FILE_PATH = 'sanity.csv'


def create_list(variation_id):
    print "Testing creating a new list ..."
    create_url = '/lists/{}/{}'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, variation_id)
    post_data = {
        "filePath": TEST_FILE_PATH,
    }

    headers = testing_utilities.generate_headers()
    return requests.put(urlparse.urljoin(configuration.data.list_loading_service_base_url, create_url),
                        data=json.dumps(post_data), headers=headers)


def list_status(variation_id):
    print "Testing created list status ..."
    status_url = '/lists/{}/{}/statistics'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, variation_id)
    headers = testing_utilities.generate_headers()
    return requests.get(urlparse.urljoin(configuration.data.list_loading_service_base_url, status_url), headers=headers)


def delete_list(variation_id):
    print "Testing deleting created list ..."
    delete_url = '/lists/{}/{}/'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, variation_id)
    headers = testing_utilities.generate_headers()
    post_data = {"filePath": TEST_FILE_PATH}
    return requests.delete(urlparse.urljoin(configuration.data.list_loading_service_base_url, delete_url),
                           data=json.dumps(post_data), headers=headers)


def check_membership(account_number, variation_id):
    print "Testing if a member exists on the created list ..."
    check_membership_url = '/lists/{}/{}/{}'.format(LIST_LOADING_SERVICE_INDEX_OFFERS_SANITY, variation_id,
                                                    account_number)
    headers = testing_utilities.generate_headers()
    return requests.get(urlparse.urljoin(configuration.data.list_loading_service_base_url, check_membership_url),
                        headers=headers)


def _get_testing_data():
    account_numbers = [
        "1c30bfeb-9a03-4144-b838-094652f28aec",
        "dff85334-2af5-492c-827d-efb7c98b2917",
        "2045ecfd-7f7c-4b04-ae27-f85af578d574",
        "2b37b80e-e89e-49d2-91b6-ccb90f59d2a4",
        "10afc5e5-18b1-4e42-b453-ca4d2e814ab0",
        # "اختبار",
        # "一二三二百",
        # "ANGÈLE",
        # "двадцать четыре"
    ]
    return len(account_numbers), random.choice(account_numbers)


@attrib.attr('application_sanity_tests', 'production_sanity_tests')
class SanityTests(base.BaseIntegrationTestCase):

    def setUp(self):
        self.variation_id = str(uuid.uuid4())

    def test_list_loading_service_succeeds(self):

        @backoff.on_exception(backoff.expo, AssertionError, max_tries=5)
        def _assert(status_code, response_status_code):
            tools.assert_equal(status_code, response_status_code)

        amount_of_account_numbers, valid_account_number = _get_testing_data()
        response = create_list(self.variation_id)
        _assert(httplib.ACCEPTED, response.status_code)

        response = list_status(self.variation_id)
        _assert(httplib.OK, response.status_code)
        tools.assert_equal(amount_of_account_numbers, response.json()['hits']['total'])

        response = check_membership(valid_account_number, self.variation_id)
        _assert(httplib.OK, response.status_code)

        response = check_membership(str(uuid.uuid4()), self.variation_id)
        _assert(httplib.NOT_FOUND, response.status_code)

        response = delete_list(self.variation_id)
        _assert(httplib.ACCEPTED, response.status_code)

        response = list_status(self.variation_id)
        _assert(httplib.NOT_FOUND, response.status_code)

    def tearDown(self):
        try:
            delete_list(self.variation_id)
        except:
            pass
