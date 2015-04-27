import logging
import csv
import os

import elasticsearch
from elasticsearch import helpers
from liblcp import cross_service


logger = logging.getLogger(__name__)


class ListProcessingService(object):
    def _elastic_search_operation(self, request):
        errors = None
        try:
            if not os.path.isfile(request.file):
                raise IOError("File does not exist")
            with open(request.file, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                actions = []
                for line in csv_reader:
                    action = {
                        "_index": request.index,
                        "_type": request.type,
                        "_id": csv_reader.line_num,
                        "_source": {
                            "id": line[0]
                        }
                    }
                    actions.append(action)
                es = elasticsearch.Elasticsearch()
                logger.info("Bulk indexing file")
                result = helpers.bulk(es, actions)
                logger.info("Finished indexing {} documents".format(result[0]))
                es.indices.refresh(index=request.index)
        except Exception as e:
            errors = True
            logging.error(e.message)
            logging.error("An error occurred when creating a new list")
        finally:
            if request.callbackUrl:
                data = {
                    'success': False if errors else True,
                    'links': {
                        'self': {
                            'href': request.url
                        }
                    }
                }
                cross_service.post(service=request.index, path=request.callbackUrl, data=data)
