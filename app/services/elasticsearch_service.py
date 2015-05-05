import logging
import traceback
import csv
import os
import configuration
import elasticsearch
import openpyxl
import httplib

from elasticsearch import helpers, exceptions

from liblcp import cross_service


logger = logging.getLogger(__name__)
logging.getLogger('elasticsearch.trace').setLevel(logging.WARN)


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

    def __enter__(self):
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
    def wrapper(self, request):
        errors = False
        try:
            f(self, request)
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
                cross_service.post_or_abort(service=request.service, path=request.callbackUrl, data=data)

    return wrapper


class ElasticSearchService(object):

    @elastic_search_callback
    def create_list(self, request):
        if not os.path.isfile(request.file):
            raise IOError("File does not exist")
        filetype = request.file.split('.')[-1]
        file_reader = CsvReader(request.file) if filetype == 'csv' else ExcelReader(request.file)
        actions = []
        with file_reader:
            for line in file_reader.get_rows():
                action = {
                    "_index": request.service,
                    "_type": request.id,
                    "_id": line,
                    "_source": {
                        "accountNumber": line
                    }
                }
                actions.append(action)

        es = elasticsearch.Elasticsearch([configuration.data.ELASTIC_SEARCH_SERVER])
        logger.info("Bulk indexing file")
        result = helpers.bulk(es, actions)
        es.indices.refresh(index=request.service)
        logger.info("Finished indexing {} documents".format(result[0]))

    def delete_list(self, request):
        es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)

        try:
            result = es.indices.delete_mapping(index=request.service, doc_type=request.id)
            logger.info("Elastic search delete response {}".format(result))
        except exceptions.TransportError as e:
            if e.status_code == httplib.NOT_FOUND:
                logger.warning("Elastic search delete request not found")
                raise LookupError
            else:
                logger.warning("Elastic search delete request exception: {}".format(e.info))
                raise e

        if 'acknowledged' in result and not result['acknowledged']:
            logger.warning("Elastic search delete response not acknowledged successfully")
            raise Exception

        return result

    def get_list_status(self, request):
        es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)
        result = es.search(index=request.service, doc_type=request.id, search_type="count")
        logger.info("elastic search response {}".format(result))
        if result['hits']['total'] == 0:
            logger.warning("Elastic search index/type - {}/{} request not found".format(request.index, request.type))
            raise LookupError
        return result
