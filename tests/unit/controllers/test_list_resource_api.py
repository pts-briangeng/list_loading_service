import unittest
import flask
import httplib
import json
import mock
import multiprocessing
import os

from nose import tools
from werkzeug.datastructures import Headers

import configuration

from app.controllers import lls_resource_api
from app import services
from tests import builders


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

    @mock.patch.object(flask, 'url_for', autospec=True)
    @mock.patch.object(multiprocessing, 'Process', autospec=True)
    def test_post(self, mock_multiprocessing, mock_url_for):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='POST',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'file': '/test/file'})):
            response = self.controller.post()
            tools.assert_equal(httplib.ACCEPTED, response[1])


class TestGetListByIdResourceController(unittest.TestCase):

    def setUp(self):
        self.controller = lls_resource_api.GetListByIdResourceController()

    def test_resource_by_id_resource_controller(self):
        tools.assert_equal('GetListByIdResourceController',
                           self.controller.resource_by_id_resource_controller.__name__)

    def test_get(self):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='GET',
                                      headers=Headers(test_sandbox_headers)):
            with tools.assert_raises(NotImplementedError):
                self.controller.get()

    def test_process_request_model(self):
        with tools.assert_raises(NotImplementedError):
            self.controller.process_request_model({})


class TestDeleteListResourceController(unittest.TestCase):

    def setUp(self):
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))
        self.controller = lls_resource_api.DeleteListResourceController()

    @mock.patch.object(services.ElasticSearch, 'delete_list', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_delete(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value = (builders.ESDeleteResponseBuilder()
                                     .with_acknowledged_response().http_response()['response'])
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='DELETE',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({})):
            response = self.controller.delete()
            tools.assert_equal(httplib.ACCEPTED, response[1])
            tools.assert_equal(mock_service.call_count, 1)
            mock_url_for.assert_called_once_with('getlistbyidresourcecontroller', _external=True)

    @mock.patch.object(services.ElasticSearch, 'delete_list', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_delete_with_errors(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.side_effect = LookupError
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='DELETE',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({})):
            response = self.controller.delete()
            tools.assert_equal(httplib.NOT_FOUND, response[1])
            tools.assert_equal(mock_service.call_count, 1)

    @mock.patch.object(services.ElasticSearch, 'delete_list', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_delete_not_acknowledged(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.side_effect = Exception
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='DELETE',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({})):
            response = self.controller.delete()
            tools.assert_equal(httplib.INTERNAL_SERVER_ERROR, response[1])
            tools.assert_equal(mock_service.call_count, 1)


class TestListStatusGetResourceController(unittest.TestCase):

    def setUp(self):
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))
        self.controller = lls_resource_api.ListStatusGetResourceController()

    @mock.patch.object(services.ElasticSearch, 'get_list_status', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_get(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value = {}
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/status',
                                      method='GET',
                                      headers=Headers(test_sandbox_headers)):
            response = self.controller.get()
            tools.assert_equal(httplib.OK, response[1])
            tools.assert_equal(mock_service.call_count, 1)
            mock_url_for.assert_called_once_with('liststatusgetresourcecontroller', _external=True)
