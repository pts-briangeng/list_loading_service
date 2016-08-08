import csv
import os
import types
import unittest
import subprocess

import mock
import openpyxl
from nose import tools

import configuration
from app.services import readers
from tests import mocks


class TestElasticSearchFileReaders(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))

    @tools.raises(Exception)
    def test_should_always_be_a_instance_of_csv_xls_reader(self):
        readers.FileReader('/content/list_upload/id.csv')

    @mock.patch.object(os.path, 'isfile', autospec=True)
    @mock.patch.object(subprocess, 'check_output', autospec=True)
    @mock.patch.object(csv, 'reader', autospec=True)
    @mock.patch.object(readers, 'open', create=True)
    def test_reads_csv_file_correctly(self, mock_open, mock_csv_reader, mock_subprocess_check_output, mock_is_file):
        mock_open.return_value = mock.MagicMock(spec=file)
        mock_csv_reader.return_value = mocks.generator(['account_no'])
        mock_subprocess_check_output.return_value = "100 filename"

        csv_reader = readers.CsvReader('/content/list_upload/id.csv')
        tools.assert_equals(mocks.Any(types.GeneratorType), csv_reader.get_rows())
        tools.assert_equals("account_no", next(csv_reader.get_rows()))
        tools.assert_false(csv_reader.is_empty())
        try:
            next(next(csv_reader.get_rows()))
        except StopIteration as e:
            tools.assert_is_not_none(e)
        tools.assert_is_none(csv_reader.close())

    @mock.patch.object(os.path, 'isfile', autospec=True)
    @mock.patch.object(openpyxl, 'load_workbook', autospec=True)
    def test_reads_excel_file_correctly(self, mock_load_workbook, mock_is_file):
        mock_cell = mock.MagicMock()
        mock_cell.value = 'account_no'
        mock_load_workbook.return_value.active.rows = mocks.generator([mock_cell])
        xl_reader = readers.ExcelReader('/content/list_upload/id.xlsx')
        mock_load_workbook.return_value.active.rows = mocks.generator([mock_cell])
        tools.assert_equals(mocks.Any(types.GeneratorType), xl_reader.get_rows())
        tools.assert_equals("account_no", next(xl_reader.get_rows()))
        tools.assert_is_none(xl_reader.close())

    @mock.patch.object(subprocess, 'check_output', autospec=True)
    @mock.patch.object(os.path, 'isfile', autospec=True)
    @mock.patch.object(openpyxl, 'load_workbook', autospec=True)
    @mock.patch.object(readers, 'open', create=True)
    def test_get_correct_reader_based_on_extension(self, mock_open, mock_load_workbook, mock_is_file,
                                                   mock_subprocess_check_output):
        mock_open.return_value = mock.MagicMock(spec=file)
        mock_subprocess_check_output.return_value = "100 filename"

        mock_cell = mock.MagicMock()
        mock_cell.value = 'account_no'
        mock_load_workbook.return_value.active.rows = mocks.generator([mock_cell])

        tools.assert_true(
            isinstance(readers.BulkAccountsFileReaders.get('/content/list_upload/id.xlsx'), readers.ExcelReader))
        tools.assert_true(
            isinstance(readers.BulkAccountsFileReaders.get('/content/list_upload/id.csv'), readers.CsvReader))
        tools.assert_true(
            isinstance(readers.BulkAccountsFileReaders.get('/content/list_upload/id.txt'), readers.CsvReader))
