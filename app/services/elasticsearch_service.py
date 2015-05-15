import json
import logging
import traceback
import csv
import os
import configuration
import elasticsearch
import openpyxl
import httplib

from elasticsearch import helpers, exceptions
from requestswrapper import requests_wrapper

from liblcp import context


logger = logging.getLogger(__name__)

MAPPING = {
    "properties": {
        "accountNumber": {
            "type": "string",
            "index": "not_analyzed"
        }
    }
}


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
                requests_wrapper.post(url=request.callbackUrl, data=json.dumps(data),
                                      headers=dict(context.get_headers(), **{'Content-Type': 'application/json'}))

    return wrapper


class ElasticSearchService(object):

    def _create_es_index_if_required(self, es, index):
        try:
            if not es.indices.exists(index=index):
                logger.info("Creating new index {}".format(index))
                es.indices.create(index=index)
        except exceptions.TransportError as e:
            logger.warning("Elastic search get index request exception: {}".format(e.info))
            raise e

    def _create_es_mapping(self, es, index, doc_type):
        try:
            es.indices.put_mapping(doc_type=doc_type, body=MAPPING, index=index)
        except exceptions.TransportError as e:
            logger.warning("Elastic search create mapping request exception: {}".format(e.info))
            raise e

    @elastic_search_callback
    def create_list(self, request):
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        if not os.path.isfile(file_path):
            raise IOError("File does not exist")
        file_type = file_path.split('.')[-1]
        file_reader = CsvReader(file_path) if file_type == 'csv' else ExcelReader(file_path)
        actions = []
        with file_reader:
            for line in file_reader.get_rows():
                action = {
                    "_index": request.service,
                    "_type": request.list_id,
                    "_id": line,
                    "_source": {
                        "accountNumber": line
                    }
                }
                actions.append(action)

        es = elasticsearch.Elasticsearch([configuration.data.ELASTIC_SEARCH_SERVER])
        self._create_es_index_if_required(es, request.service)
        self._create_es_mapping(es, request.service, request.list_id)

        logger.info("Bulk indexing file")
        result = helpers.bulk(es, actions)
        es.indices.refresh(index=request.service)
        logger.info("Finished indexing {} documents".format(result[0]))

    def delete_list(self, request):
        file_path = os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath)
        es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)

        try:
            logger.info("Elasticsearch is deleting index: {}, doc_type: {}".format(request.service, request.list_id))
            result = es.indices.delete_mapping(index=request.service, doc_type=request.list_id)
            logger.info("Elastic search delete response {}".format(result))
        except exceptions.TransportError as e:
            if e.status_code == httplib.NOT_FOUND:
                logger.warning("Elastic search delete request not found")
                raise LookupError
            else:
                logger.warning("Elastic search delete request exception: {}".format(e.info))
                raise e

        if not result.get('acknowledged', False):
            logger.warning("Elastic search delete response not acknowledged successfully")
            raise Exception

        try:
            os.remove(file_path)
        except OSError as e:
            logger.warning("Error deleting file: {}".format(e))

        return result

    def get_list_status(self, request):
        es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)
        result = es.search(index=request.service, doc_type=request.list_id, search_type="count")
        logger.info("elastic search response {}".format(result))
        if result['hits']['total'] == 0:
            logger.warning("Elastic search index/type - {}/{} request not found".format(request.service,
                                                                                        request.list_id))
            raise LookupError
        return result

    def get_list_member(self, request):
        es = elasticsearch.Elasticsearch(configuration.data.ELASTIC_SEARCH_SERVER)
        if not es.exists(index=request.service, doc_type=request.list_id, id=request.member_id):
            raise LookupError
        return {}
