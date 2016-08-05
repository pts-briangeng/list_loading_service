import httplib
import logging
import multiprocessing
import traceback

from restframework import controllers
from werkzeug import exceptions as flask_errors

from app import exceptions, models, services
from app.controllers import base
from app.controllers.schemas import put_list, delete_list, append_list

logger = logging.getLogger(__name__)


class CreateListPutResourceController(base.BaseListResourceController, controllers.PutResourceController):

    __resource__ = '/lists/<service>/<list_id>'

    def __init__(self):
        super(CreateListPutResourceController, self).__init__(schema=put_list.REQUEST)
        self.http_successful_response_status = httplib.ACCEPTED

    @property
    def resource_by_id_resource_controller(self):
        return CreateListPutResourceController

    def process_request_model(self, request_model, **kwargs):
        request = models.Request(url=self.request_url, **dict(request_model, **kwargs))
        multiprocessing.Process(target=services.ElasticSearch().create_list, args=(request,)).start()
        return {}


class GetListByIdResourceController(base.BaseListResourceController, controllers.GetResourceController):

    NOT_FOUND_DESCRIPTION = flask_errors.NotFound.description
    __resource__ = '/lists/<service>/<list_id>/'

    def __init__(self):
        super(GetListByIdResourceController, self).__init__()

    @property
    def resource_by_id_resource_controller(self):
        return GetListByIdResourceController

    def process_request_model(self, request_model, **kwargs):
        raise NotImplementedError


class DeleteListResourceController(base.BaseListResourceController, controllers.DeleteResourceController):

    __resource__ = '/lists/<service>/<list_id>/'

    def __init__(self):
        super(DeleteListResourceController, self).__init__(schema=delete_list.REQUEST,
                                                           exception_translations=exceptions.EXCEPTION_TRANSLATIONS)
        self.http_successful_response_status = httplib.ACCEPTED

    @property
    def resource_by_id_resource_controller(self):
        return GetListByIdResourceController

    def process_request_model(self, request_model, **kwargs):
        request = models.Request(url=self.request_url, **dict(request_model, **kwargs))
        response = services.ElasticSearch().delete_list(request)
        return response


class ListStatusGetResourceController(base.BaseListResourceController, controllers.GetResourceController):

    __resource__ = '/lists/<service>/<list_id>/statistics'

    def __init__(self):
        super(ListStatusGetResourceController, self).__init__(exception_translations=exceptions.EXCEPTION_TRANSLATIONS)

    @property
    def resource_by_id_resource_controller(self):
        return ListStatusGetResourceController

    def get(self, **kwargs):
        try:
            request = models.Request(url=self.request_url, **kwargs)
            response_model = services.ElasticSearch().get_list_status(request)
        except Exception as e:
            logger.exception("An error occurred in get stats for the list {} - {}".format(kwargs.get('list_id'),
                                                                                          traceback.format_exc()))
            return self.translate_exceptions(e)
        response_dict = self.create_restful_response_payload(response_model, **kwargs)
        response_headers = self.create_response_headers(response_dict)
        return response_dict, httplib.OK, response_headers


class GetListMemberByIdResourceController(base.BaseListResourceController, controllers.GetResourceController):

    NOT_FOUND_DESCRIPTION = flask_errors.NotFound.description
    __resource__ = '/lists/<service>/<list_id>/members/<member_id>'

    def __init__(self):
        super(GetListMemberByIdResourceController, self).__init__(
            exception_translations=exceptions.EXCEPTION_TRANSLATIONS)

    @property
    def resource_by_id_resource_controller(self):
        return GetListMemberByIdResourceController

    def get(self, **kwargs):
        try:
            request = models.Request(url=self.request_url, **kwargs)
            response_model = services.ElasticSearch().get_list_member(request)
        except Exception as e:
            logger.exception(u"An error occurred in get member {} for the list {} - {}".format(kwargs.get('member_id'),
                                                                                               kwargs.get('list_id'),
                                                                                               traceback.format_exc()))
            return self.translate_exceptions(e)
        response_dict = self.create_restful_response_payload(response_model, **kwargs)
        response_headers = self.create_response_headers(response_dict)
        return response_dict, httplib.OK, response_headers


class AppendListPutResourceController(base.BaseListResourceController, controllers.PutResourceController):

    __resource__ = '/lists/<service>/<list_id>/members'

    def __init__(self):
        super(AppendListPutResourceController, self).__init__(schema=append_list.REQUEST,
                                                              exception_translations=exceptions.EXCEPTION_TRANSLATIONS)
        self.http_successful_response_status = httplib.OK

    @property
    def resource_by_id_resource_controller(self):
        return AppendListPutResourceController

    def process_request_model(self, request_model, **kwargs):
        request = models.Request(url=self.request_url, **dict(request_model, **kwargs))
        return services.ElasticSearch().append_list(request)
