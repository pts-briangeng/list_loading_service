import logging
import service_container

logger = logging.getLogger(__name__)

"""
List Loading Service:
"""


class ListLoadingService(service_container.base.BaseService):
    def __init__(self, name, import_name, *args, **kwargs):
        super(ListLoadingService, self).__init__(name, import_name, *args, **kwargs)

    def service_url_prefix(self):
        return ''


service = ListLoadingService('list_loading_service', __name__)
