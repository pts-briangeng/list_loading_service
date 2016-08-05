import httplib
import json
import multiprocessing
import os
import unittest

import flask
import mock
from nose import tools
from werkzeug.datastructures import Headers

import configuration
from app import exceptions
from app.controllers import lls_resource_api
from tests import builders

test_sandbox_headers = {
    'Content-Type': 'application/json',
    'PTS-LCP-CID': '123',
    'PTS-LCP-Mode': 'sandbox',
    'PTS-LCP-Principal': 'https://sandbox.lcpenv/security/principals/1001-0100-0011',
    'PTS-LCP-Base-URL': 'https://sandbox.lcpenv'}


class TestCreateListPutResourceController(unittest.TestCase):

    def setUp(self):
        self.controller = lls_resource_api.CreateListPutResourceController()

    def test_put_empty(self):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='PUT',
                                      headers=Headers(test_sandbox_headers),
                                      data={}):
            response = self.controller.put()
            tools.assert_equal(httplib.BAD_REQUEST, response[1])

    @mock.patch.object(flask, 'url_for', autospec=True)
    @mock.patch.object(multiprocessing, 'Process', autospec=True)
    def test_put(self, mock_multiprocessing, mock_url_for):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='PUT',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'filePath': '/test/file'})):
            response = self.controller.put()
            tools.assert_equal(httplib.ACCEPTED, response[1])


class TestGetListByIdResourceController(unittest.TestCase):

    def setUp(self):
        self.controller = lls_resource_api.GetListByIdResourceController()

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

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_delete(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.delete_list.return_value = (builders.ESDeleteResponseBuilder()
                                                              .with_acknowledged_response().http_response()['response'])
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='DELETE',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'filePath': 'file'})):
            response = self.controller.delete()
            tools.assert_equal(httplib.ACCEPTED, response[1])
            tools.assert_equal(mock_service.return_value.delete_list.call_count, 1)
            mock_url_for.assert_called_once_with(
                lls_resource_api.GetListByIdResourceController.__name__.lower(), _external=True)

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_delete_with_errors(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.delete_list.side_effect = LookupError
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='DELETE',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'filePath': 'file'})):
            response = self.controller.delete()
            tools.assert_equal(httplib.NOT_FOUND, response[1])
            tools.assert_equal(mock_service.return_value.delete_list.call_count, 1)

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_delete_not_acknowledged(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.delete_list.side_effect = Exception
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42',
                                      method='DELETE',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'filePath': 'file'})):
            response = self.controller.delete()
            tools.assert_equal(httplib.INTERNAL_SERVER_ERROR, response[1])
            tools.assert_equal(mock_service.return_value.delete_list.call_count, 1)


class TestListStatusGetResourceController(unittest.TestCase):

    def setUp(self):
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))
        self.controller = lls_resource_api.ListStatusGetResourceController()

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_get(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.get_list_status.return_value = {}
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/status',
                                      method='GET',
                                      headers=Headers(test_sandbox_headers)):
            response = self.controller.get()
            tools.assert_equal(httplib.OK, response[1])
            tools.assert_equal(mock_service.return_value.get_list_status.call_count, 1)
            mock_url_for.assert_called_once_with(self.controller.__class__.__name__.lower(), _external=True)

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_get_not_found(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.get_list_status.side_effect = LookupError
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/status',
                                      method='GET',
                                      headers=Headers(test_sandbox_headers)):
            response = self.controller.get()
            tools.assert_equal(httplib.NOT_FOUND, response[1])
            tools.assert_equal(mock_service.return_value.get_list_status.call_count, 1)


class TestListMemberGetResourceController(unittest.TestCase):

    def setUp(self):
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))
        self.controller = lls_resource_api.GetListMemberByIdResourceController()

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_get(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.get_list_member.return_value = {}
        with app.test_request_context('/app/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/123',
                                      method='GET',
                                      headers=Headers(test_sandbox_headers)):
            response = self.controller.get()
            tools.assert_equal(httplib.OK, response[1])
            tools.assert_equal(mock_service.return_value.get_list_member.call_count, 1)
            mock_url_for.assert_called_once_with(self.controller.__class__.__name__.lower(), _external=True)

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_get_not_found(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.get_list_member.side_effect = LookupError
        with app.test_request_context('/app/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/123',
                                      method='GET',
                                      headers=Headers(test_sandbox_headers)):
            response = self.controller.get()
            tools.assert_equal(httplib.NOT_FOUND, response[1])
            tools.assert_equal(mock_service.return_value.get_list_member.call_count, 1)


class TestAppendListPutResourceController(unittest.TestCase):

    def setUp(self):
        self.controller = lls_resource_api.AppendListPutResourceController()

    def test_append_empty(self):
        app = flask.Flask(__name__)
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/members',
                                      method='PUT',
                                      headers=Headers(test_sandbox_headers),
                                      data={}):
            response = self.controller.put()
            tools.assert_equal(httplib.BAD_REQUEST, response[1])

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_append(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.append_list.return_value = {}
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/members',
                                      method='PUT',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'filePath': '/test/file'})):
            response = self.controller.put()
            tools.assert_equal(httplib.OK, response[1])

    @mock.patch('app.controllers.lls_resource_api.services.ElasticSearch', autospec=True)
    @mock.patch.object(flask, 'url_for', autospec=True)
    def test_append_too_big_file(self, mock_url_for, mock_service):
        app = flask.Flask(__name__)
        mock_service.return_value.append_list.side_effect = exceptions.FileTooBigError
        with app.test_request_context('/index/app/type/6d04bd2d-da75-420f-a52a-d2ffa0c48c42/members',
                                      method='PUT',
                                      headers=Headers(test_sandbox_headers),
                                      data=json.dumps({'filePath': '/test/file'})):
            response = self.controller.put()
            tools.assert_equal(httplib.BAD_REQUEST, response[1])
            expected_response = {'errors': [{'code': 'BAD_REQUEST',
                                             'description': 'There are too many lists currently being processed.',
                                             'field': None}]}
            tools.assert_equal(expected_response, response[0])
