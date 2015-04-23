import logging

from liblcp import cross_service

logger = logging.getLogger(__name__)


class ListProcessingService(object):

    def _elastic_search_operation(self, request):
        errors = None
        try:
            # The call(s) to ES will go here
            pass
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
