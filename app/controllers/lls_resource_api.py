import httplib
import multiprocessing
import logging

from restframework import controllers, errors
from werkzeug import exceptions as flask_errors

from app.controllers import base
from app.controllers.schemas import post_list, post_empty
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
        multiprocessing.Process(target=services.ListProcessing().create_list, args=(request,)).start()
        return {}


class GetListByIdResourceController(base.BaseListResourceController, controllers.GetResourceController):
    NOT_FOUND_DESCRIPTION = flask_errors.NotFound.description

    def __init__(self):
        super(GetListByIdResourceController, self).__init__()

    @property
    def resource_by_id_resource_controller(self):
        return GetListByIdResourceController

    def process_request_model(self, request_model, **kwargs):
        raise NotImplementedError


class DeleteListResourceController(base.BaseListResourceController, controllers.DeleteResourceController):

    def __init__(self):
        super(DeleteListResourceController, self).__init__(schema=post_empty.REQUEST,
                                                           exception_translations={
                                                               Exception: (httplib.NOT_FOUND,
                                                                           errors.NOT_FOUND,
                                                                           'Could not find type to delete.')
                                                           })
        self.http_successful_response_status = httplib.ACCEPTED

    @property
    def resource_by_id_resource_controller(self):
        return GetListByIdResourceController

    def process_request_model(self, request_model, **kwargs):
        request = models.Request(url=self.request_url, **dict(request_model, **kwargs))
        response = services.ListProcessing().delete_list(request)
        if 'status' in response and response['status'] == httplib.NOT_FOUND:
            raise LookupError
        return response


class ListStatusGetResourceController(base.BaseListResourceController, controllers.GetResourceController):

    @property
    def resource_by_id_resource_controller(self):
        return ListStatusGetResourceController

    def get_resource_model(self, resource):
        request = models.Request(url=self.request_url, **resource)
        return services.ListProcessing().get_list_status(request)
