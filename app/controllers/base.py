import logging
from collections import namedtuple
import flask

from restframework import controllers
from werkzeug import exceptions as flask_exceptions


logger = logging.getLogger(__name__)

RequestContext = namedtuple('RequestContext', ['principal', 'mode', 'external_base_host_url'])


class BaseListResourceController(controllers.BaseResourceController):

    """
    Mixin to combine the similar functionality found in all the List Loading Service resource controllers.
    """

    NOT_FOUND_DESCRIPTION = flask_exceptions.NotFound.description

    @property
    def resource_model_key_mappings(self):
        return {}

    @property
    def resource_by_id_resource_controller(self):
        return self.__class__

    @property
    def request_url(self):
        return flask.request.url

    def create_restful_response_payload(self, response_model, **kwargs):
        response_dict = self.model_to_dict(response_model)
        response_dict = self.add_links_to_response_payload(response_dict, **kwargs)
        return response_dict

    def add_links_to_response_payload(self, response_json, **kwargs):
        response_json['links'] = {
            'self': {'href': self.create_self_link_url(response_json, **kwargs)}
        }
        return response_json

    def create_self_link_url(self, response_json, **kwargs):
        single_item_endpoint_name = self.resource_by_id_resource_controller.__name__.lower()

        resource = {}
        if isinstance(self.resource_model_key_mappings, dict):
            resource = {key: response_json.get(value, '') for key, value in
                        self.resource_model_key_mappings.iteritems()}

        resource.update(kwargs)

        resource['_external'] = getattr(resource, '_external', True)
        url = flask.url_for(single_item_endpoint_name, **resource)
        return self.compute_resource_url(url)
