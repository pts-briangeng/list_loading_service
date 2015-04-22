from restframework import controllers

from list_loading_app import models
from list_loading_app.controllers import base
from list_loading_app.controllers.schemas import post_empty


class ListLoadingServicePostResourceController(base.ResourceControllerMixin, controllers.PostResourceController):

    def __init__(self):
        super(ListLoadingServicePostResourceController, self).__init__(schema=post_empty.REQUEST)

    @property
    def resource_by_id_resource_controller(self):
        return ListLoadingServicePostResourceController

    def process_request_model(self, request_model, **kwargs):
        return {}
