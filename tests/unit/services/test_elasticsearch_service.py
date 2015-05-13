import json
import unittest
import os
import csv
import copy
import httplib
import uuid

import mock
from liblcp import context
import elasticsearch
import openpyxl
from elasticsearch import helpers, exceptions
from nose import tools

from app.services import elasticsearch_service
import configuration
from app import models, services


class CsvMock(list):
    line_num = 1L


class MockCell(object):

    def __init__(self, cell_value):
        self.cell_value = cell_value

    @property
    def value(self):
        return self.cell_value


class MockHttpResponse(object):

    def __init__(self, status_code=httplib.OK, response=None):
        self.status_code = status_code
        self.response = response

    def json(self):
        return self.response

    def status_code(self):
        return self.status_code

    def raise_for_status(self):
        if self.status_code not in [httplib.OK, httplib.CREATED]:
            raise Exception


CORRELATION_ID = str(uuid.uuid4())
PRINCIPAL = str(uuid.uuid4())
context.set_headers_getter(lambda name: {context.HEADERS_EXTERNAL_BASE_URL: 'http://localhost',
                                         context.HEADERS_CORRELATION_ID: CORRELATION_ID,
                                         context.HEADERS_MODE: context.MODE_LIVE,
                                         context.HEADERS_PRINCIPAL: PRINCIPAL}[name])


class TestElasticSearchService(unittest.TestCase):

    def setUp(self):
        self.data = {
            'url': 'url',
            'file': 'file.csv',
            'service': 'service',
            'list_id': 'id',
            'callbackUrl': 'callback',
        }
        self.member_data = copy.deepcopy(self.data)
        self.member_data['member_id'] = 'member_id'
        self.service = services.ElasticSearch()
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))

    @mock.patch.object(elasticsearch_service.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(helpers, 'bulk', autospec=True)
    @mock.patch.object(configuration, 'data', autospec=True)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    @mock.patch.object(csv, 'reader', autospec=True)
    @mock.patch.object(services.elasticsearch_service, 'open', create=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_elastic_search_operation_with_csv(self, mock_is_file, mock_open, mock_csv_reader, mock_elastic_search,
                                               mock_config, mock_bulk, mock_requests_wrapper_post):
        mock_open.return_value = mock.MagicMock(spec=file)
        mock_csv_reader.return_value = CsvMock([['abc']])

        mock_elastic_search.return_value = mock.MagicMock()
        mock_requests_wrapper_post.return_value = MockHttpResponse(httplib.OK, {})
        request = models.Request(**self.data)

        self.service.create_list(request)

        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     [{'_type': 'service', '_source': {'listId': 'id', 'accountNumber': 'abc'},
                                       '_index': 'service'}])
        mock_elastic_search.return_value.indices.refresh.assert_called_with(index='service')
        mock_requests_wrapper_post.assert_has_calls([
            mock.call(url='callback',
                      headers={
                          'PTS-LCP-Base-URL': 'http://localhost',
                          'PTS-LCP-Mode': context.MODE_LIVE,
                          'PTS-LCP-CID': CORRELATION_ID,
                          'PTS-LCP-Principal': PRINCIPAL,
                          'Content-Type': 'application/json'
                      },
                      data=json.dumps({
                          'success': True,
                          'links': {
                              'self': {
                                  'href': 'url'
                              }
                          }
                      })
                      )
        ])

    @mock.patch.object(elasticsearch_service.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(helpers, 'bulk', autospec=True)
    @mock.patch.object(configuration, 'data', autospec=True)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    @mock.patch.object(openpyxl, 'load_workbook', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_elastic_search_operation_excel(self, mock_is_file, mock_load_workbook, mock_elastic_search, mock_config,
                                            mock_bulk, mock_requests_wrapper_post):
        mock_load_workbook.return_value.active.rows = [[MockCell('abc')]]

        mock_elastic_search.return_value = mock.MagicMock()
        mock_requests_wrapper_post.return_value = MockHttpResponse(httplib.OK, {})
        data = copy.deepcopy(self.data)
        data['file'] = 'file.xlsx'
        request = models.Request(**data)
        self.service.create_list(request)

        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     [{'_type': 'service', '_source': {'listId': 'id', 'accountNumber': 'abc'},
                                       '_index': 'service'}])
        mock_elastic_search.return_value.indices.refresh.assert_called_with(index='service')
        mock_requests_wrapper_post.assert_has_calls([
            mock.call(url='callback',
                      headers={
                          'PTS-LCP-Base-URL': 'http://localhost',
                          'PTS-LCP-Mode': context.MODE_LIVE,
                          'PTS-LCP-CID': CORRELATION_ID,
                          'PTS-LCP-Principal': PRINCIPAL,
                          'Content-Type': 'application/json'
                      },
                      data=json.dumps({
                          'success': True,
                          'links': {
                              'self': {
                                  'href': 'url'
                              }
                          }
                      })
                      )
        ])

    @mock.patch.object(elasticsearch_service.requests_wrapper, 'post', autospec=True)
    def test_elastic_search_operation_without_callback(self, mock_requests_wrapper_post):
        self.data.pop('callbackUrl')
        mock_requests_wrapper_post.return_value = MockHttpResponse(httplib.OK, {})
        request = models.Request(**self.data)
        self.service.create_list(request)
        mock_requests_wrapper_post.assert_has_calls([])

    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_delete_list(self, mock_elastic_search):
        mock_elastic_search.return_value = mock.MagicMock()
        request = models.Request(**self.data)
        self.service.delete_list(request)
        mock_elastic_search.return_value.delete_by_query.assert_called_once_with(
            body={'query': {'match': {'listId': 'id'}}},
            doc_type='service',
            index='service')

    @tools.raises(LookupError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_delete_list_not_found(self, mock_elastic_search):
        not_found_exception = exceptions.TransportError(404,
                                                        'IndexMissingException[[123] missing]',
                                                        {'status': 400, 'error': 'IndexMissingException[[123] missing]'}
                                                        )
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.delete_by_query.side_effect = not_found_exception
        request = models.Request(**self.data)
        self.service.delete_list(request)

    @tools.raises(exceptions.TransportError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_delete_list_general_error(self, mock_elastic_search):
        general_exception = exceptions.TransportError(500, 'Server error', {'status': 500, 'error': 'Server error'})
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.delete_by_query.side_effect = general_exception
        request = models.Request(**self.data)
        self.service.delete_list(request)

    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_status(self, mock_elastic_search):
        request = models.Request(**self.data)
        response = self.service.get_list_status(request)
        tools.assert_equal(mock_elastic_search.return_value.search.return_value, response)
        mock_elastic_search.return_value.search.assert_called_once_with(
            index='service',
            doc_type='service',
            body={'query': {'match': {'listId': 'id'}}},
            search_type='count')

    @tools.raises(LookupError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_status_throws_404_when_count_0(self, mock_elastic_search):
        mock_elastic_search.return_value.search.return_value = {"hits": {"total": 0}}
        request = models.Request(**self.data)
        self.service.get_list_status(request)

    @tools.raises(LookupError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_status_throws_404_when_transport_error(self, mock_elastic_search):
        not_found_exception = exceptions.TransportError(
            404,
            'IndexMissingException[[123] missing]',
            {'status': 404, 'error': 'IndexMissingException[[123] missing]'})
        mock_elastic_search.return_value.search.side_effect = not_found_exception
        request = models.Request(**self.data)
        self.service.get_list_status(request)

    @tools.raises(exceptions.TransportError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_status_throws_exceptions_when_error(self, mock_elastic_search):
        mock_elastic_search.return_value.search.side_effect = exceptions.TransportError(400,
                                                                                        'Error',
                                                                                        {'status': 400,
                                                                                         'error': 'Error'})
        request = models.Request(**self.data)
        response = self.service.get_list_status(request)
        print response

    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_member(self, mock_elastic_search):
        mock_elastic_search.return_value.search.return_value = {"hits": {"total": 5}}
        request = models.Request(**self.member_data)
        response = self.service.get_list_member(request)
        tools.assert_equal({}, response)
        mock_elastic_search.return_value.search.assert_called_once_with(
            body={'query': {'bool': {'must': [{'match': {'listId': 'id'}},
                                              {'match': {'accountNumber': 'member_id'}}]}}},
            doc_type='service', index='service')

    @tools.raises(LookupError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_member_not_found(self, mock_elastic_search):
        mock_elastic_search.return_value.search.return_value = {"hits": {"total": 0}}
        request = models.Request(**self.member_data)
        self.service.get_list_member(request)

    @tools.raises(LookupError)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_member_when_404(self, mock_elastic_search):
        not_found_exception = exceptions.TransportError(
            404,
            'IndexMissingException[[123] missing]',
            {'status': 404, 'error': 'IndexMissingException[[123] missing]'})
        mock_elastic_search.return_value.search.side_effect = not_found_exception
        request = models.Request(**self.member_data)
        self.service.get_list_member(request)

    @tools.raises(Exception)
    @mock.patch.object(elasticsearch, 'Elasticsearch', autospec=True)
    def test_list_member_when_execption(self, mock_elastic_search):
        request_error = exceptions.TransportError(
            400,
            'Error',
            {'status': 400, 'error': 'Error'})
        mock_elastic_search.return_value.search.side_effect = request_error
        request = models.Request(**self.member_data)
        self.service.get_list_member(request)
