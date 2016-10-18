import os
import json
import logging
import traceback
import configuration

from liblcp import context
from requestswrapper import requests_wrapper

import functools

logger = logging.getLogger(__name__)


def upload_cleanup(f):
    def wrapper(request):
        result = f(request)
        try:
            os.remove(os.path.join(configuration.data.VOLUME_MAPPINGS_FILE_UPLOAD_TARGET, request.filePath))
            logger.info("File {} deleted".format(request.filePath))
        except OSError as e:
            logger.warning("Error deleting file: {}".format(e))
        finally:
            return result
    return wrapper


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
                if not errors:
                    data['links']['member'] = {
                        'href': '/{}/{}/{{member-id}}'.format(request.service, request.list_id)
                    }

                requests_wrapper.post(url=request.callbackUrl, data=json.dumps(data),
                                      headers=dict(context.get_headers(), **{'Content-Type': 'application/json'}))

    return wrapper


def elastic_search_query_params(*params):

    def wrapper(f):
        @functools.wraps(f)
        def inner_wrapper(*args, **kwargs):
            filtered_kwargs = {param: kwargs.get(param, None) for param in params if param in kwargs}

            return f(*args, **filtered_kwargs)

        return inner_wrapper
    return wrapper
