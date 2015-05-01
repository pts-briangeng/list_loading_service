import logging
import elasticsearch_service

logger = logging.getLogger(__name__)


class ListProcessingService(object):

    def create_list(self, request):
        elasticsearch_service.create_list(request)

    def delete_list(self, request):
        return elasticsearch_service.delete_list(request)

    def get_list_status(self, request):
        return elasticsearch_service.get_list_status(request)
