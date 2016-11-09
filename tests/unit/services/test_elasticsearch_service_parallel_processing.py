import copy
import httplib
import os
import types
import unittest

import mock
from elasticsearch import helpers
from nose import tools

import base
import configuration
from app import models
from app.services import readers, clients, decorators
from tests import mocks

configuration.configure_from(
    os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service_parallel_processing_enabled.cfg'))


class TestElasticSearchServiceParallelProcessing(base.BaseTestElasticSearchService):

    def setUp(self):
        super(TestElasticSearchServiceParallelProcessing, self).setUp()
        configuration.configure_from(
            os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service_parallel_processing_enabled.cfg'))

    @unittest.skipIf(
        configuration.data.LIST_PARALLEL_BULK_PROCESSING_ENABLED is False, "Bulk parallel processing enabled")
    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(helpers, 'parallel_bulk', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_create_list_with_csv_with_parallel_bulk_processing(
            self, mock_is_file, mock_elastic_search, mock_bulk, mock_requests_wrapper_post, mock_bulk_reader_get,
            mock_os_rename):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.indices.exists.return_value = False
        mock_requests_wrapper_post.return_value = mocks.MockHttpResponse(httplib.OK, {})
        request = models.Request(**self.data)
        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        accounts_list = [["account_no_{}".format(account_number_index)] for account_number_index in xrange(10000)]
        mock_csv_reader.get_rows.return_value = accounts_list
        mock_bulk_reader_get.get.return_value = mock_csv_reader
        mock_bulk.return_value = (accounts_list, None,)

        self.service.create_list(request)

        args, _ = mock_bulk.call_args
        tools.assert_equals(type(args[1]), types.GeneratorType)
        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     mocks.Any(types.GeneratorType),
                                     thread_count=4,
                                     index='service',
                                     chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE,
                                     doc_type='id')
        mock_elastic_search.return_value.indices.refresh.assert_called_once_with(index='service')
        self._assert_callback(mock_requests_wrapper_post, True, 'id.csv')

    @unittest.skipIf(
        configuration.data.LIST_PARALLEL_BULK_PROCESSING_ENABLED is False, "Bulk parallel processing enabled")
    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(helpers, 'parallel_bulk', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_elastic_search_operation_excel_with_parallel_bulk_processing(
            self, mock_is_file, mock_elastic_search, mock_bulk, mock_requests_wrapper_post, mock_bulk_reader_get,
            mock_os_rename):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_requests_wrapper_post.return_value = mocks.MockHttpResponse(httplib.OK, {})
        data = copy.deepcopy(self.data)
        data['filePath'] = 'file.xlsx'
        request = models.Request(**data)
        mock_xl_reader = mock.MagicMock(autospec=readers.ExcelReader)
        mock_xl_reader.is_empty.return_value = False
        accounts_list = [["account_no_{}".format(account_number_index)] for account_number_index in xrange(10000)]
        mock_xl_reader.get_rows.return_value = accounts_list
        mock_bulk_reader_get.get.return_value = mock_xl_reader
        mock_bulk.return_value = (accounts_list, None,)

        self.service.create_list(request)

        args, _ = mock_bulk.call_args
        tools.assert_equals(type(args[1]), types.GeneratorType)
        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     mocks.Any(types.GeneratorType),
                                     thread_count=4,
                                     index='service',
                                     chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE,
                                     doc_type='id')
        mock_elastic_search.return_value.indices.refresh.assert_called_with(index='service')
        self._assert_callback(mock_requests_wrapper_post, True, 'id.xlsx')
