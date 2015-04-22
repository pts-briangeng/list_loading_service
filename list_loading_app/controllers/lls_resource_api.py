from list_loading_app.controllers import base
from restframework import controllers


class ListLoadingServicePostResourceController(base.ResourceControllerMixin, controllers.PostResourceController):

    def __init__(self):
        super(ListLoadingServicePostResourceController, self).__init__()

    def process_request_model(self, request_model, **kwargs):

        return kwargs