import unittest

from nose import tools

from list_loading_app import list_loading_service


class OffersServiceTestCase(unittest.TestCase):

    def test_service_url_prefix(self):
        service = list_loading_service.ListLoadingService(name='name', import_name='import_name')
        tools.assert_equal('', service.service_url_prefix())
