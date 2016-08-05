import copy
import httplib
import json
import os
import types
import unittest

import mock
from elasticsearch import helpers, exceptions
from nose import tools

import base
import configuration
from app import models, exceptions as app_exceptions
from app.services import readers, clients, decorators
from tests import builders, mocks

configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))


class TestElasticSearchService(base.BaseTestElasticSearchService):

    def setUp(self):
        super(TestElasticSearchService, self).setUp()

    @unittest.skipIf(
        configuration.data.LIST_PARALLEL_BULK_PROCESSING_ENABLED is True, "Bulk parallel processing not enabled")
    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(helpers, 'bulk', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_create_list_with_csv(self, mock_is_file, mock_elastic_search, mock_bulk, mock_requests_wrapper_post,
                                  mock_bulk_reader_get, mock_os_rename):

        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.indices.exists.return_value = False
        mock_requests_wrapper_post.return_value = mocks.MockHttpResponse(httplib.OK, {})
        request = models.Request(**self.data)
        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        mock_csv_reader.get_rows.return_value = [
            ["account_no_{}".format(account_number_index)] for account_number_index in xrange(10000)]
        mock_bulk_reader_get.get.return_value = mock_csv_reader

        self.service.create_list(request)

        args, _ = mock_bulk.call_args
        tools.assert_equals(type(args[1]), types.GeneratorType)
        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     mocks.Any(types.GeneratorType),
                                     index='service',
                                     chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE,
                                     doc_type='id')
        mock_elastic_search.return_value.indices.refresh.assert_called_once_with(index='service')
        self._assert_callback(mock_requests_wrapper_post, True, 'id.csv')

    @unittest.skipIf(
        configuration.data.LIST_PARALLEL_BULK_PROCESSING_ENABLED is True, "Bulk parallel processing not enabled")
    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(helpers, 'bulk', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_elastic_search_operation_excel(self, mock_is_file, mock_elastic_search, mock_bulk,
                                            mock_requests_wrapper_post, mock_bulk_reader_get, mock_os_rename):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_requests_wrapper_post.return_value = mocks.MockHttpResponse(httplib.OK, {})
        data = copy.deepcopy(self.data)
        data['filePath'] = 'file.xlsx'
        request = models.Request(**data)
        mock_xl_reader = mock.MagicMock(autospec=readers.ExcelReader)
        mock_xl_reader.is_empty.return_value = False
        mock_xl_reader.get_rows.return_value = [
            ["account_no_{}".format(account_number_index)] for account_number_index in xrange(10000)]
        mock_bulk_reader_get.get.return_value = mock_xl_reader

        self.service.create_list(request)

        args, _ = mock_bulk.call_args
        tools.assert_equals(type(args[1]), types.GeneratorType)
        mock_bulk.assert_called_with(mock_elastic_search.return_value,
                                     mocks.Any(types.GeneratorType),
                                     index='service',
                                     chunk_size=configuration.data.BULK_PROCESSING_CHUNK_SIZE,
                                     doc_type='id')
        mock_elastic_search.return_value.indices.refresh.assert_called_with(index='service')
        self._assert_callback(mock_requests_wrapper_post, True, 'id.xlsx')

    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    def test_elastic_search_operation_without_callback(self, mock_requests_wrapper_post):
        self.data.pop('callbackUrl')
        mock_requests_wrapper_post.return_value = mocks.MockHttpResponse(httplib.OK, {})
        request = models.Request(**self.data)

        self.service.create_list(request)

        mock_requests_wrapper_post.assert_has_calls([])

    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_create_throws_error_on_bulk_call(self, mock_is_file, mock_elastic_search, mock_requests_wrapper_post,
                                              mock_bulk_reader_get, mock_os_rename):

        mock_serializer = mock.MagicMock()
        mock_serializer.dumps = lambda *args: json.dumps(args[0])
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.transport = mock.MagicMock()
        mock_elastic_search.return_value.transport.serializer = mock_serializer
        mock_elastic_search.return_value.bulk.side_effect = base.INTERNAL_SERVER_ERROR_EXCEPTION
        mock_requests_wrapper_post.return_value = mocks.MockHttpResponse(httplib.OK, {})
        request = models.Request(**self.data)

        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        mock_csv_reader.get_rows.return_value = ["account_no"]
        mock_bulk_reader_get.get.return_value = mock_csv_reader

        self.service.create_list(request)

        tools.assert_equal(0, mock_elastic_search.return_value.indices.refresh.call_count)
        mock_elastic_search.return_value.bulk.assert_called_once_with(
            "\n".join([
                json.dumps({'index': {'_type': 'id', '_id': 'account_no', '_index': 'service'}}),
                json.dumps({'accountNumber': 'account_no'})]) + "\n",
            index='service',
            doc_type='id')
        tools.assert_equal(1, mock_elastic_search.return_value.bulk.call_count)
        tools.assert_equal(0, mock_elastic_search.return_value.indices.put_mapping.call_count)
        tools.assert_equal(0, mock_elastic_search.return_value.indices.refresh.call_count)
        self._assert_callback(mock_requests_wrapper_post, False, "TransportError(500, 'Server error')")

    @mock.patch.object(decorators.logger, 'error', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_create_list_logs_and_returns_error_on_non_existent_csv_file(
            self, mock_is_file, mock_requests_wrapper_post, mock_logger):
        mock_is_file.return_value = False
        request = models.Request(**self.data)

        self.service.create_list(request)

        mock_logger.assert_has_calls(mock.call('An error occurred when creating a new list: File '
                                               '/content/list_upload/file.csv does not exist!'))
        self._assert_callback(mock_requests_wrapper_post, False, "File /content/list_upload/file.csv does not exist!")

    @mock.patch.object(decorators.logger, 'error', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_create_list_logs_and_returns_error_on_empty_csv_file(
            self, mock_is_file, mock_requests_wrapper_post, mock_os_rename, mock_bulk_reader_get, mock_logger):
        request = models.Request(**self.data)

        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = True
        mock_csv_reader.get_rows.return_value = ["account_no"]
        mock_bulk_reader_get.get.return_value = mock_csv_reader

        self.service.create_list(request)

        mock_logger.assert_has_calls(mock.call('An error occurred when creating a new list: File '
                                               '/content/list_upload/file.csv is empty!'))
        self._assert_callback(mock_requests_wrapper_post, False)

    @mock.patch.object(decorators.logger, 'error', autospec=True)
    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(os, 'rename', autospec=True)
    @mock.patch.object(decorators.requests_wrapper, 'post', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    def test_create_list_logs_and_returns_error_on_empty_xlsx_file(
            self, mock_is_file, mock_requests_wrapper_post, mock_os_rename, mock_bulk_reader_get, mock_logger):
        data = copy.deepcopy(self.data)
        data['filePath'] = 'file.xlsx'
        request = models.Request(**data)

        mock_csv_reader = mock.MagicMock(autospec=readers.ExcelReader)
        mock_csv_reader.is_empty.return_value = True
        mock_csv_reader.get_rows.return_value = ["account_no"]
        mock_bulk_reader_get.get.return_value = mock_csv_reader

        self.service.create_list(request)

        mock_logger.assert_has_calls(mock.call('An error occurred when creating a new list: File '
                                               '/content/list_upload/file.xlsx is empty!'))
        self._assert_callback(mock_requests_wrapper_post, False, "File /content/list_upload/file.xlsx is empty!")

    @mock.patch.object(os, 'remove')
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_delete_list(self, mock_elastic_search, mock_remove):
        mock_elastic_search.return_value = mock.MagicMock()
        request = models.Request(**self.data)

        self.service.delete_list(request)

        mock_elastic_search.return_value.indices.delete_mapping.assert_called_once_with(
            doc_type='id', index='service')
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        mock_remove.assert_called_once_with(file_path)

    @tools.raises(LookupError)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_delete_list_not_found(self, mock_elastic_search):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.indices.delete_mapping.side_effect = base.NOT_FOUND_EXCEPTION
        request = models.Request(**self.data)

        self.service.delete_list(request)

    @tools.raises(exceptions.TransportError)
    @mock.patch.object(os, 'remove')
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_delete_list_general_error(self, mock_elastic_search, mock_remove):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.indices.delete_mapping.side_effect = base.INTERNAL_SERVER_ERROR_EXCEPTION
        request = models.Request(**self.data)

        self.service.delete_list(request)
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        mock_remove.assert_called_once_with(file_path)

    @tools.raises(Exception)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_delete_list_not_acknowledged(self, mock_elastic_search):
        mock_elastic_search.return_value = mock.MagicMock()
        mock_elastic_search.return_value.indices.delete_mapping.return_value = (
            builders.ESDeleteResponseBuilder().with_unacknowledged_response().http_response()['response'])
        request = models.Request(**self.data)

        self.service.delete_list(request)

    @mock.patch.object(os, 'remove')
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_delete_list_os_raises_exception(self, mock_elastic_search, mock_remove):
        mock_elastic_search.return_value = mock.MagicMock()
        request = models.Request(**self.data)
        mock_remove.side_effect = OSError

        self.service.delete_list(request)

        mock_elastic_search.return_value.indices.delete_mapping.assert_called_once_with(
            doc_type='id', index='service')
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        mock_remove.assert_called_once_with(file_path)

    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_list_status(self, mock_elastic_search):
        request = models.Request(**self.data)

        response = self.service.get_list_status(request)

        tools.assert_equal(mock_elastic_search.return_value.search.return_value, response)
        mock_elastic_search.return_value.search.assert_called_once_with(
            doc_type='id', index='service', search_type='count')

    @tools.raises(LookupError)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_list_status_throws_404_when_count_0(self, mock_elastic_search):
        mock_elastic_search.return_value.search.return_value = {"hits": {"total": 0}}
        request = models.Request(**self.data)

        self.service.get_list_status(request)

    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_list_member(self, mock_elastic_search):
        mock_elastic_search.return_value.exists.return_value = True
        request = models.Request(**self.member_data)

        response = self.service.get_list_member(request)

        tools.assert_equal({}, response)
        mock_elastic_search.return_value.exists.assert_called_once_with(doc_type='id', index='service', id='member_id')

    @tools.raises(LookupError)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_list_member_not_found(self, mock_elastic_search):
        mock_elastic_search.return_value.exists.return_value = False
        request = models.Request(**self.member_data)

        response = self.service.get_list_member(request)

        tools.assert_equal({}, response)
        mock_elastic_search.return_value.exists.assert_called_once_with(doc_type='id', index='service', id='member_id')

    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(os, 'remove')
    @mock.patch.object(helpers, 'bulk', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    def test_append_list(self, mock_elastic_search, mock_is_file, mock_bulk, mock_remove, mock_bulk_reader_get):
        mock_elastic_search.return_value = mock.MagicMock()
        request = models.Request(**self.data)

        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        mock_csv_reader.get_rows.return_value = ["account_no_{}".format(account_number_index)
                                                 for account_number_index in xrange(50)]
        mock_bulk_reader_get.get.return_value = mock_csv_reader
        failed = ["account_no_{}".format(account_number_index) for account_number_index in xrange(49)]
        mock_bulk.return_value = (1, failed)

        result = self.service.append_list(request)
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        mock_remove.assert_called_once_with(file_path)
        tools.assert_list_equal(failed, result['failed'])
        tools.assert_list_equal(['account_no_49'], result['succeeded'])

    @mock.patch.object(readers, 'BulkAccountsFileReaders', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    @mock.patch.object(clients, 'ElasticSearchClient', autospec=True)
    @tools.raises(app_exceptions.FileTooBigError)
    def test_append_list_file_too_big(self, mock_elastic_search, mock_is_file, mock_bulk_reader_get):
        mock_elastic_search.return_value = mock.MagicMock()
        request = models.Request(**self.data)

        mock_csv_reader = mock.MagicMock(autospec=readers.CsvReader)
        mock_csv_reader.is_empty.return_value = False
        mock_csv_reader.get_rows.return_value = [
            ["account_no_{}".format(account_number_index)] for account_number_index in xrange(51)]
        mock_bulk_reader_get.get.return_value = mock_csv_reader

        self.service.append_list(request)
