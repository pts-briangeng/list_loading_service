import json
import logging
import os
import traceback

from liblcp import context
from requestswrapper import requests_wrapper

logger = logging.getLogger(__name__)


def rename_file(request_file, request_list):
    def rreplace(s, old, new, occurrence):
        li = s.rsplit(old, occurrence)
        return new.join(li)

    file_name, _ = os.path.splitext(os.path.basename(request_file))
    return rreplace(request_file, file_name, request_list, 1)


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
                    'file': rename_file(request.filePath, request.list_id),
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
