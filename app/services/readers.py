import abc
import csv
import os

import openpyxl


class FileReader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, filename):
        self.filename = filename
        if not os.path.isfile(filename):
            raise IOError("File {} does not exist!".format(filename))
        self.descriptor = self._get_descriptor()
        self.line_in_file = self._get_number_of_lines()
        if self.is_empty():
            raise EOFError("File {} is empty!".format(filename))

    @abc.abstractmethod
    def _get_descriptor(self):
        pass

    @abc.abstractmethod
    def _get_number_of_lines(self):
        pass

    @abc.abstractmethod
    def get_rows(self):
        pass

    def is_empty(self):
        return self.line_in_file == 0

    def is_exceed_max_line_limit(self, max_limit):
        return self.line_in_file > max_limit

    @abc.abstractmethod
    def close(self):
        pass


class CsvReader(FileReader):

    def __init__(self, filename):
        super(CsvReader, self).__init__(filename)

    def _get_descriptor(self):
        return open(self.filename, 'rU')

    def _get_number_of_lines(self):
        return sum(1 for _ in self.get_rows())

    def close(self):
        self.descriptor.close()

    def get_rows(self):
        for row in csv.reader(self.descriptor):
            yield row[0]


class ExcelReader(FileReader):

    def __init__(self, filename):
        super(ExcelReader, self).__init__(filename)
        if self.is_empty():
            raise EOFError("File {} is empty!".format(filename))

    def _get_number_of_lines(self):
        return sum(1 for _ in self.descriptor.rows)

    def _get_descriptor(self):
        workbook = openpyxl.load_workbook(self.filename, read_only=True)
        return workbook.active

    def get_rows(self):
        for row in self.descriptor.rows:
            yield row[0].value

    def close(self):
        pass


class BulkAccountsFileReaders(object):

    @classmethod
    def get(cls, file_path):
        file_type = file_path.split('.')[-1].lower()
        if file_type in ['csv', 'txt']:
            return CsvReader(file_path)
        return ExcelReader(file_path)
