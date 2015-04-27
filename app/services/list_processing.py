import elasticsearch_service


class ListProcessingService(object):

    def create_list(self, request):
        elasticsearch_service.create_list(request)
