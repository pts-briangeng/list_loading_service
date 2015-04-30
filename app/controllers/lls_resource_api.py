import httplib
import multiprocessing
import logging

from restframework import controllers

from app.controllers import base
from app.controllers.schemas import post_list
from app import services
from app import models

logger = logging.getLogger(__name__)


class CreateListPostResourceController(base.BaseListResourceController, controllers.PostResourceController):

    def __init__(self):
        super(CreateListPostResourceController, self).__init__(schema=post_list.REQUEST)
        self.http_successful_response_status = httplib.ACCEPTED

    @property
    def resource_by_id_resource_controller(self):
        return CreateListPostResourceController

    def process_request_model(self, request_model, **kwargs):
        request = models.Request(url=self.request_url, **dict(request_model, **kwargs))
        multiprocessing.Process(target=services.ElasticSearch().create_list, args=(request,)).start()
        return {}


class ListStatusGetResourceController(base.BaseListResourceController, controllers.GetResourceController):

    @property
    def resource_by_id_resource_controller(self):
        return ListStatusGetResourceController

    def get_resource_model(self, resource):
        request = models.Request(url=self.request_url, **resource)
        return services.ElasticSearch().get_list_status(request)
