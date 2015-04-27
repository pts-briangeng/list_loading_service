import json
import os
import unittest

import configuration
import fabfile

from tests.integration import testing_utilities

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
        cls.stub_lcp = testing_utilities.StubServer.make_stub_lcp()

    def setUp(self):
        self.stub_lcp.clear()

    @classmethod
    def tearDownClass(cls):
        cls.stub_lcp.teardown()

    def queue_stub_response(self, *stub_responses):
        for stub_response in stub_responses:
            self.stub_lcp.queue_response(status_code=stub_response.get("status_code"),
                                         text=json.dumps(stub_response.get("response")))
