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
        self.descriptor = None

    @abc.abstractmethod
    def get_rows(self):
        pass

    @staticmethod
    def count(descriptor=None, max_limit_count=1):
        index = 0
        for index, row in enumerate(descriptor, start=1):
            if index <= max_limit_count:
                continue
            else:
                break
        return index < (max_limit_count - 1)

    def is_empty(self, descriptor=None):
        return self.count(descriptor=descriptor, max_limit_count=1)

    @abc.abstractmethod
    def exceeds_allowed_row_count(self, descriptor=None, max_limit_count=1):
        return not self.count(descriptor=descriptor, max_limit_count=max_limit_count)

    @abc.abstractmethod
    def close(self):
        pass


class CsvReader(FileReader):

    def __init__(self, filename):
        super(CsvReader, self).__init__(filename)
        self.descriptor = open(self.filename, 'rU')
        if super(CsvReader, self).is_empty(self.descriptor):
            raise EOFError("File {} is empty!".format(filename))

    def close(self):
        self.descriptor.close()

    def exceeds_allowed_row_count(self, **kwargs):
        return super(CsvReader, self).exceeds_allowed_row_count(
            csv.reader(self.descriptor), kwargs.get("max_limit_count"))

    def get_rows(self):
        self.descriptor = open(self.filename, 'rU')
        for row in csv.reader(self.descriptor):
            yield row[0]


class ExcelReader(FileReader):

    def __init__(self, filename):
        super(ExcelReader, self).__init__(filename)
        workbook = openpyxl.load_workbook(self.filename, read_only=True)
        self.descriptor = workbook.active
        if super(ExcelReader, self).is_empty(self.descriptor.rows):
            raise EOFError("File {} is empty!".format(filename))

    def exceeds_allowed_row_count(self, **kwargs):
        return super(ExcelReader, self).exceeds_allowed_row_count(self.descriptor.rows, kwargs.get("max_limit_count"))

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
