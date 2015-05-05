import unittest

from nose import tools

from app import models


class TestModels(unittest.TestCase):

    def test_request(self):
        request = models.Request()
        tools.assert_equal(request.url, '')
        tools.assert_equal(request.file, '')
        tools.assert_equal(request.service, '')
        tools.assert_equal(request.callbackUrl, '')

    def test_request_with_data(self):
        data = {
            'url': 'url',
            'file': 'file',
            'service': 'service',
            'id': 'id',
            'callbackUrl': 'callback',
        }
        request = models.Request(**data)
        tools.assert_equal(request.url, 'url')
        tools.assert_equal(request.file, 'file')
        tools.assert_equal(request.service, 'service')
        tools.assert_equal(request.id, 'id')
        tools.assert_equal(request.callbackUrl, 'callback')
