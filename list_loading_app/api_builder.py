import logging

from liblcp import configuration as lcp_config
from liblcp import context as lcp_context
from restframework import rest_api

from list_loading_app import app_logging, instrumentation
from list_loading_app.controllers import lls_resource_api


logger = logging.getLogger(__name__)


class ApiConfiguration(object):
    profiled_targets = []

    def __init__(self, flask_app):
        self.api = rest_api.RestApi(flask_app)
        self.setup_endpoints()
        instrumentation.instrument(ApiConfiguration.profiled_targets, logger.getEffectiveLevel())

    def setup_endpoints(self):
        pass
        # self.api.add_resource(lls_resource_api.ListLoadingServicePostResourceController, '/<index>/<type>/<id>')


def build_server():
    import configuration
    import flask
    import service_container

    flask_app = flask.Flask(__name__)
    container = service_container.ServiceContainer(flask_app)
    container.api = ApiConfiguration(flask_app)

    configuration.data = configuration.Container(**container.app.config['LIST_LOADING_SERVICE'])
    connect_lcp_context_to_app_context(flask_app)
    app_logging.install_required_root_formatter()

    return flask_app


def connect_lcp_context_to_app_context(flask_app):
    import flask

    def get_header_value(name):
        return flask.request.headers.get(name)

    def set_headers_getter():
        lcp_context.set_headers_getter(get_header_value)

    lcp_config.set_configuration(flask_app.config.copy())
    lcp_context.set_headers_getter(set_headers_getter)
    flask_app.before_request(set_headers_getter)
