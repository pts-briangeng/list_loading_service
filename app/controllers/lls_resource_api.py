import httplib
import multiprocessing
import logging

from restframework import controllers

from app.controllers import base
from app.controllers.schemas import post_list
from app import services
from app import models

logger = logging.getLogger(__name__)


class CreateListPostResourceController(base.ResourceControllerMixin, controllers.PostResourceController):
    def __init__(self):
        super(CreateListPostResourceController, self).__init__(schema=post_list.REQUEST)
        self.http_successful_response_status = httplib.ACCEPTED

    @property
    def resource_by_id_resource_controller(self):
        return CreateListPostResourceController

    def process_request_model(self, request_model, **kwargs):
        url = self.request_url
        index = kwargs.get("index", "")
        type = kwargs.get("type", "")
        callback_url = request_model.get("callbackUrl", "")
        file = request_model.get("file", "")
        request = models.Request(url=url, index=index, type=type, file=file, callbackUrl=callback_url)

        multiprocessing.Process(target=services.ListProcessing().create_list, args=(request,)).start()

        return {}


class ListStatusGetResourceController(base.ResourceControllerMixin, controllers.GetResourceController):

    @property
    def resource_by_id_resource_controller(self):
        return ListStatusGetResourceController

    def get_resource_model(self, resource):
        url = self.request_url
        index = resource.get("index", "")
        type = resource.get("type", "")
        request = models.Request(url=url, index=index, type=type)
        return services.ListProcessing().get_list_status(request)
