import json
import os
import unittest
import uuid

from elasticsearch import exceptions
from liblcp import configuration as liblcp_config, context

import configuration
import fabfile
from tests.integration import servers

CONFIGURATION_PATH = fabfile.configuration_path
INTEGRATION_TEST_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_PROJECT_PATH = os.path.join(INTEGRATION_TEST_PATH, '..', '..')


class BaseIntegrationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._configure_test()

    @staticmethod
    def _configure_test():
        configuration_filename = os.environ['TEST_CONFIG']
        configuration_path = os.path.abspath(os.path.join(INTEGRATION_TEST_PATH, 'configuration'))
        configuration_file_path = os.path.abspath(os.path.join(configuration_path, configuration_filename))
        configuration.configure_from(configuration_file_path)

        app_configuration = os.path.join(
            configuration.data.configuration_dir if os.path.isabs(configuration.data.configuration_dir)
            else os.path.abspath(os.path.join(configuration_path, configuration.data.configuration_dir)),
            'list_loading_service.cfg')
        configuration.configure_from(app_configuration)


class BaseIntegrationLiveStubServerTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.stub_lcp = servers.StubServer.make_stub_server()
        cls.headers = {context.HEADERS_EXTERNAL_BASE_URL: 'http://live.lcpenv',
                       context.HEADERS_CORRELATION_ID: str(uuid.uuid4()),
                       context.HEADERS_MODE: 'sandbox',
                       context.HEADERS_PRINCIPAL: str(uuid.uuid4())}
        context.set_headers_getter(lambda name: cls.headers[name])

    def setUp(self):
        self.stub_lcp.clear()

    @classmethod
    def tearDownClass(cls):
        cls.stub_lcp.teardown()

    def queue_stub_response(self, *stub_responses):
        for stub_response in stub_responses:
            self.stub_lcp.queue_response(status_code=stub_response.get("status_code"),
                                         text=json.dumps(stub_response.get("response")))

    def queue_transport_error(self):
        not_found_exception = exceptions.TransportError(404, 'Not Found', {'status': 400, 'error': 'Not found'})
        self.stub_lcp.queue_error(not_found_exception)


def retry_if_assertion_error(exception):
    return isinstance(exception, AssertionError)


class BaseFullIntegrationTestCase(BaseIntegrationTestCase, BaseIntegrationLiveStubServerTestCase):

    @classmethod
    def setUpClass(cls):
        BaseIntegrationTestCase._configure_test()
        BaseFullIntegrationTestCase._configure_liblcp()
        BaseIntegrationLiveStubServerTestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        BaseIntegrationLiveStubServerTestCase.tearDownClass()

    @staticmethod
    def _configure_liblcp():
        liblcp_config_data = {}
        execfile(os.path.abspath(os.path.join(BASE_PROJECT_PATH, 'configuration', 'servicecontainer.cfg')),
                 liblcp_config_data)
        liblcp_config.set_configuration(liblcp_config_data)


class ListPaths(object):

    @classmethod
    def create(cls, **kwargs):
        if kwargs.get('relative_url', False):
            return '/lists/{service}/{list_id}'.format(**kwargs)
        return '{base_url}/lists/{service}/{list_id}'.format(**kwargs)

    @classmethod
    def append(cls, **kwargs):
        if kwargs.get('relative_url', False):
            return '/lists/{service}/{list_id}/members/'.format(**kwargs)
        return '{base_url}/lists/{service}/{list_id}/members/'.format(**kwargs)

    @classmethod
    def stats(cls, **kwargs):
        if kwargs.get('relative_url', False):
            return '/lists/{service}/{list_id}/statistics'.format(**kwargs)
        return '{base_url}/lists/{service}/{list_id}/statistics'.format(**kwargs)

    @classmethod
    def callback_url(cls, **kwargs):
        return '{base_url}/offers/{offer_id}/variations/{list_id}/list/complete'.format(**kwargs)

    @classmethod
    def delete(cls, **kwargs):
        if kwargs.get('relative_url', False):
            return '/lists/{service}/{list_id}/'.format(**kwargs)
        return '{base_url}/lists/{service}/{list_id}/'.format(**kwargs)

    @classmethod
    def get_list_member(cls, **kwargs):
        if kwargs.get('relative_url', False):
            return '/lists/{service}/{list_id}/members/{member_id}'.format(**kwargs)
        return '{base_url}/lists/{service}/{list_id}/members/{member_id}'.format(**kwargs)

    @classmethod
    def delete_from_list(cls, **kwargs):
        if kwargs.get('relative_url', False):
            return '{base_url}/lists/<service>/<list_id>/members/'.format(**kwargs)
        return '{base_url}/lists/<service>/<list_id>/members/'.format(**kwargs)
