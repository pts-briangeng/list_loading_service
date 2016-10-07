# -*- coding: UTF-8 -*-

import copy
import httplib
import json
import time
import urllib

import backoff
import requests
from liblcp import urls
from nose import tools

from tests.integration import base


def assert_list_create(request_data, path_params, headers):
    response = requests.put(base.ListPaths.create(**path_params), json.dumps(request_data), headers=headers)
    response_content = response.json()
    tools.assert_equal(httplib.ACCEPTED, response.status_code)
    tools.assert_in(base.ListPaths.create(relative_url=True, **path_params), urls.self_link(response_content))


def assert_append_to_list(request_data, path_params, headers):
    response = requests.put(base.ListPaths.append(**path_params), json.dumps(request_data), headers=headers)
    response_content = response.json()
    tools.assert_equal(httplib.OK, response.status_code)
    tools.assert_in(base.ListPaths.append(relative_url=True, **path_params), urls.self_link(response_content))


def assert_delete_from_list(request_data, path_params, headers):
    response = requests.delete(base.ListPaths.append(**path_params), data=json.dumps(request_data), headers=headers)
    response_content = response.json()
    tools.assert_equal(httplib.OK, response.status_code)
    tools.assert_in(base.ListPaths.append(relative_url=True, **path_params), urls.self_link(response_content))


@backoff.on_exception(backoff.expo, AssertionError, max_tries=10)
def assert_search_for_created_list(path_params, accounts_count, headers):
    response = requests.get(base.ListPaths.stats(**path_params), headers=headers)
    response_content = response.json()

    tools.assert_equal(httplib.OK, response.status_code)
    tools.assert_in(base.ListPaths.stats(relative_url=True, **path_params), urls.self_link(response_content))
    tools.assert_equal(accounts_count, response_content['hits']['total'])


def assert_search_for_member_in_list(path_params, headers):
    response = requests.get(base.ListPaths.get_list_member(**path_params), headers=headers)

    tools.assert_equal(httplib.OK, response.status_code)
    response_content = response.json()
    tools.assert_in(urllib.quote(base.ListPaths.get_list_member(relative_url=True, **path_params)),
                    urls.self_link(response_content).encode('UTF-8'))


def assert_member_not_found_in_list(path_params, headers, member_id=None):
    params = copy.deepcopy(path_params)
    params['member_id'] = member_id or "XXXXXXX"
    response = requests.get(base.ListPaths.get_list_member(**params), headers=headers)

    tools.assert_equal(httplib.NOT_FOUND, response.status_code)


def assert_list_delete(path_params, headers):
    response = requests.delete(base.ListPaths.delete(**path_params), data=json.dumps({}), headers=headers)
    response_content = response.json()

    tools.assert_equal(httplib.ACCEPTED, response.status_code)
    tools.assert_in(base.ListPaths.create(relative_url=True, **path_params), urls.self_link(response_content))
    tools.assert_true(response_content['acknowledged'])
    time.sleep(2)


def assert_deleted_list_cannot_be_accessed(path_params, headers):
    response = requests.get(base.ListPaths.stats(**path_params), headers=headers)
    tools.assert_equal(httplib.NOT_FOUND, response.status_code)


@backoff.on_exception(backoff.expo, AssertionError, max_tries=10)
def assert_list_functionality(request_data, path_params, accounts_count, headers, assert_create=True):

    if assert_create:
        assert_list_create(request_data, path_params, headers)

    assert_search_for_created_list(path_params, accounts_count, headers)
    assert_search_for_member_in_list(path_params, headers)
    assert_member_not_found_in_list(path_params, headers)
    assert_list_delete(path_params, headers)
    assert_deleted_list_cannot_be_accessed(path_params, headers)
