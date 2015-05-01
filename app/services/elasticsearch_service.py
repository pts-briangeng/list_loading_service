import logging
import traceback
import csv
import os
import configuration
import elasticsearch
import openpyxl

from elasticsearch import helpers

from liblcp import cross_service


logger = logging.getLogger(__name__)


class FileReader(object):
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_rows(self):
        pass


class CsvReader(FileReader):
    def __init__(self, filename):
        super(CsvReader, self).__init__(filename)
        print "init"

    def __enter__(self):
        print "enter"
        self.csv_file = open(self.filename, 'r')
        return self.csv_file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.csv_file.close()

    def get_rows(self):
        for row in csv.reader(self.csv_file):
            yield row[0]


class ExcelReader(FileReader):
    def __init__(self, filename):
        super(ExcelReader, self).__init__(filename)

    def __enter__(self):
        self.workbook = openpyxl.load_workbook(self.filename, read_only=True)
        self.worksheet = self.workbook.active
        return self.worksheet

    def get_rows(self):
        for row in self.worksheet.rows:
            yield row[0].value


def elastic_search_callback(f):
    def wrapper(request):
        errors = False
        try:
            f(request)
        except Exception as e:
            errors = True
            logger.error('An error occurred when creating a new list: {}'.format(e.message))
            logger.error(traceback.format_exc(), exc_info=1)
        finally:
            if request.callbackUrl:
                data = {
                    'success': not errors,
                    'links': {
                        'self': {
                            'href': request.url
                        }
                    }
                }
                cross_service.post_or_abort(service=request.index, path=request.callbackUrl, data=data)

    return wrapper


@elastic_search_callback
def create_list(request):
    if not os.path.isfile(request.file):
        raise IOError("File does not exist")
    filetype = request.file.split('.')[-1]
    file_reader = CsvReader(request.file) if filetype == 'csv' else ExcelReader(request.file)
    actions = []
    with file_reader:
        for line in file_reader.get_rows():
            action = {
                "_index": request.index,
                "_type": request.type,
                "_id": line,
                "_source": {
                    "accountNumber": line
                }
            }
            actions.append(action)

    es = elasticsearch.Elasticsearch([configuration.data.ELASTIC_SEARCH_SERVER])
    logger.info("Bulk indexing file")
    result = helpers.bulk(es, actions)
    es.indices.refresh(index=request.index)
    logger.info("Finished indexing {} documents".format(result[0]))


def delete_list(request):
    es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)
    result = es.indices.delete_mapping(index=request.index, doc_type=request.type)
    logger.info("Elastic search delete response {}".format(result))
    return result


def get_list_status(request):
    es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)
    result = es.search(index=request.index, doc_type=request.type, search_type="count")
    logger.info("elastic search response {}".format(result))
    return result
