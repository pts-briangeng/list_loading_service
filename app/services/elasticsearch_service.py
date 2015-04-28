import logging
import traceback
import csv
import os
import configuration
import elasticsearch
from elasticsearch import helpers
from liblcp import cross_service


logger = logging.getLogger(__name__)


def elastic_search_operation(f):
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


@elastic_search_operation
def create_list(request):
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
        es = elasticsearch.Elasticsearch([configuration.data.ELASTIC_SEARCH_SERVER])
        logger.info("Bulk indexing file")
        result = helpers.bulk(es, actions)
        logger.info("Finished indexing {} documents".format(result[0]))
        es.indices.refresh(index=request.index)
