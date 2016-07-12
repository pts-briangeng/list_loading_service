import abc
import csv
import os

import openpyxl


class FileReader(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, filename):
        self.filename = filename
        self.descriptor = None

    @abc.abstractmethod
    def get_rows(self):
        pass

    @abc.abstractmethod
    def is_empty(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass


class CsvReader(FileReader):

    def __init__(self, filename):
        super(CsvReader, self).__init__(filename)
        self.descriptor = open(filename, 'rU')

    def close(self):
        self.descriptor.close()

    def get_rows(self):
        for row in csv.reader(self.descriptor):
            yield row[0]

    def is_empty(self):
        return os.stat(self.filename).st_size == 0


class ExcelReader(FileReader):

    def __init__(self, filename):
        super(ExcelReader, self).__init__(filename)
        self.workbook = openpyxl.load_workbook(self.filename, read_only=True)
        self.descriptor = self.workbook.active

    def get_rows(self):
        for row in self.descriptor.rows:
            yield row[0].value

    def is_empty(self):
        return sum(1 for _ in self.descriptor.rows) == 0

    def close(self):
        pass


class BulkAccountsFileReaders(object):

    @classmethod
    def get(cls, file_path):
        file_type = file_path.split('.')[-1].lower()
        if file_type in ['csv', 'txt']:
            return CsvReader(file_path)
        return ExcelReader(file_path)
