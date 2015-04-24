import unittest
import flask
import httplib
import json
import mock
import multiprocessing

from nose import tools
from werkzeug.datastructures import Headers

from app.controllers import lls_resource_api


test_sandbox_headers = {
    'Content-Type': 'application/json',
    'PTS-LCP-CID': '123',
    'PTS-LCP-Mode': 'sandbox',
    'PTS-LCP-Principal': 'https://sandbox.lcpenv/security/principals/1001-0100-0011',
    'PTS-LCP-Base-URL': 'https://sandbox.lcpenv'}


class TestCreateListPostResourceController(unittest.TestCase):

    def setUp(self):
        self.controller = lls_resource_api.CreateListPostResourceController()

    def test_resource_by_id_resource_controller(self):
        tools.assert_equal('CreateListPostResourceController',
                           self.controller.resource_by_id_resource_controller.__name__)

    def test_post_empty(self):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='POST',
                                      headers=Headers(test_sandbox_headers),
                                      data={}):
            response = self.controller.post()
            tools.assert_equal(httplib.BAD_REQUEST, response[1])

    @mock.patch.object(flask, 'url_for')
    @mock.patch.object(multiprocessing, 'Process')
    def test_post(self, mock_multiprocessing, mock_url_for):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='POST',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'file': '/test/file'})):
            response = self.controller.post()
            tools.assert_equal(httplib.ACCEPTED, response[1])
