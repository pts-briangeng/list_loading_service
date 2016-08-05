import json
import logging
import traceback

from liblcp import context
from requestswrapper import requests_wrapper

logger = logging.getLogger(__name__)


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
                if not errors:
                    data['links']['member'] = {
                        'href': '/{}/{}/{{member-id}}'.format(request.service, request.list_id)
                    }

                requests_wrapper.post(url=request.callbackUrl, data=json.dumps(data),
                                      headers=dict(context.get_headers(), **{'Content-Type': 'application/json'}))

    return wrapper
