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
            'list_id': 'id',
            'member_id': 'member_id',
            'callbackUrl': 'callback',
        }
        request = models.Request(**data)
        tools.assert_equal(request.url, 'url')
        tools.assert_equal(request.file, 'file')
        tools.assert_equal(request.service, 'service')
        tools.assert_equal(request.list_id, 'id')
        tools.assert_equal(request.member_id, 'member_id')
        tools.assert_equal(request.callbackUrl, 'callback')
