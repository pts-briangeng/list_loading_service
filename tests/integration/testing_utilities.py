import BaseHTTPServer
from collections import namedtuple
import httplib
import os
import logging
import sys
import configuration
import uuid
import json
import threading
import urlparse
from fabrika.tasks import testing
from liblcp import context


logger = logging.getLogger(__name__)


CannedResponse = namedtuple('CannedResponse', 'status_code text')


class StubHttpServer(BaseHTTPServer.HTTPServer):

    def __init__(self, *args, **kwargs):
        # Cannot use super(), because HTTPServer inherits from SocketServer which is an OLD-STYLE CLASS
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kwargs)
        self.clear()

    def queue_response(self, status_code=httplib.OK, text=''):
        self._post_responses.append(CannedResponse(status_code=status_code, text=text))

    def queue_error(self, error):
        self._post_responses.append(error)

    def pop_response(self):
        try:
            return self._post_responses.pop()
        except IndexError:
            _write_line("Trying to pop a non-existent response from the stack!!!!")
            raise

    def clear(self):
        self.requests = []
        self._post_responses = []


def _write_line(line):
    sys.stderr.write("{}\n".format(line))


class StubHttpRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def log_message(self, *args, **kwargs):
        if os.environ.get('LOG_LCP_REQUESTS', False):
            _write_line("")
            _write_line("Request:")
            _write_line("---------------")
            _write_line(self.requestline)
            _write_line("")
            _write_line("Headers:")
            for header_key, header_value in self.headers.items():
                _write_line(header_key + ":" + header_value)
            _write_line("")
            try:
                _write_line("" if not self.payload else json.loads(self.payload))
            except:
                _write_line(self.payload)

    def do_POST(self):
        response = self.server.pop_response()
        if not response:
            return
        self._send_response(response, 'POST')

    def do_DELETE(self):
        response = self.server.pop_response()
        if not response:
            return
        self._send_response(response, 'DELETE')

    def do_PATCH(self):
        response = self.server.pop_response()
        self._send_response(response, 'PATCH')

    def do_PUT(self):
        response = self.server.pop_response()
        if not response:
            return
        self._send_response(response, 'PUT')

    def do_GET(self):
        response = self.server.pop_response()
        if not response:
            return
        self.method = 'GET'
        self._send_response(response, 'GET')

    def do_HEAD(self):
        response = self.server.pop_response()
        if not response:
            return
        self.method = 'HEAD'
        self._send_response(response, 'HEAD')

    def _send_response(self, response, method):
        self.method = method
        length = int(self.headers.get('Content-Length', 0))
        self.payload = self.rfile.read(length)
        self.server.requests.append(self)
        self.send_response(response.status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        try:
            self.wfile.write(response.text)
        except AttributeError:
            if not isinstance(response, Exception):
                raise

        if os.environ.get('LOG_LCP_REQUESTS', False):
            _write_line("Response:")
            _write_line("---------------")
            _write_line("")
            _write_line(response.text)
            _write_line("")


class StubServer(object):

    lcp_url = "http://0.0.0.0:5001/"

    def __init__(self, server_url):
        url_parts = urlparse.urlparse(server_url)
        self.server = StubHttpServer((url_parts.hostname, url_parts.port), StubHttpRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        testing.TestIntegrationTask.wait_for_port(url_parts.hostname, url_parts.port)
        logger.info('Stub server started on {}'.format((url_parts.hostname, url_parts.port)))

    def teardown(self):
        if self.server:
            self.server.shutdown()
            self.server.socket.close()
            while self.thread.isAlive():
                self.thread.join()

    @property
    def requests(self):
        return self.server.requests

    @property
    def requests_paths(self):
        return [r.path for r in self.requests]

    def queue_response(self, *args, **kwargs):
        return self.server.queue_response(*args, **kwargs)

    def queue_error(self, error):
        return self.server.queue_error(error)

    def clear(self, *args, **kwargs):
        return self.server.clear(*args, **kwargs)

    def __nonzero__(self):
        return bool(self.server)

    __bool__ = __nonzero__

    @classmethod
    def make_stub_lcp(cls):
        return cls(StubServer.lcp_url)


def generate_headers(mode=context.MODE_SANDBOX,
                     base_url=None,
                     cid=None,
                     principal=None):
    return dict({'Content-Type': 'application/json',
                 context.HEADERS_MODE: mode,
                 context.HEADERS_EXTERNAL_BASE_URL: configuration.data.list_loading_service_base_url,
                 context.HEADERS_CORRELATION_ID: cid or str(uuid.uuid4()),
                 context.HEADERS_PRINCIPAL: principal or configuration.data.lcp_principal})
