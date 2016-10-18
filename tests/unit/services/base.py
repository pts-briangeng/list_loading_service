import copy
import httplib
import json
import os
import unittest
import uuid

import mock
from elasticsearch import exceptions
from liblcp import context

import configuration
from app import services

CORRELATION_ID = str(uuid.uuid4())
PRINCIPAL = str(uuid.uuid4())
context.set_headers_getter(lambda name: {context.HEADERS_EXTERNAL_BASE_URL: 'http://localhost',
                                         context.HEADERS_CORRELATION_ID: CORRELATION_ID,
                                         context.HEADERS_MODE: context.MODE_LIVE,
                                         context.HEADERS_PRINCIPAL: PRINCIPAL}[name])

NOT_FOUND_EXCEPTION = exceptions.TransportError(httplib.NOT_FOUND,
                                                'IndexMissingException[[123] missing]',
                                                {
                                                    'status': httplib.BAD_REQUEST,
                                                    'error': 'IndexMissingException[[123] missing]'
                                                })

INTERNAL_SERVER_ERROR_EXCEPTION = exceptions.TransportError(httplib.INTERNAL_SERVER_ERROR,
                                                            'Internal Server error',
                                                            {
                                                                'status': httplib.INTERNAL_SERVER_ERROR,
                                                                'error': 'Server error'
                                                            })


DELETE_BY_QUERY_RESPONSE_BODY = {
                                  "_indices": {
                                    "service": {
                                      "_shards": {
                                        "total": 5,
                                        "successful": 5,
                                        "failed": 0
                                      }
                                    }
                                  }
                                }


class BaseTestElasticSearchService(unittest.TestCase):

    def setUp(self):
        self.data = {
            'url': 'url',
            'filePath': 'file.csv',
            'service': 'service',
            'list_id': 'id',
            'callbackUrl': 'callback',
        }
        self.member_data = copy.deepcopy(self.data)
        self.member_data['member_id'] = 'member_id'
        self.service = services.ElasticSearch()
        configuration.configure_from(os.path.join(configuration.CONFIGURATION_PATH, 'list_loading_service.cfg'))

    @staticmethod
    def _assert_callback(mock_requests_wrapper_post, success, error=None):
        data = {
            'success': success,
            'links': {
                'self': {
                    'href': 'url'
                }
            }
        }
        if success:
            data['links']['member'] = {'href': '/service/id/{member-id}'}

        mock_requests_wrapper_post.assert_has_calls([
            mock.call(url='callback',
                      headers={
                          'PTS-LCP-Base-URL': 'http://localhost',
                          'PTS-LCP-Mode': context.MODE_LIVE,
                          'PTS-LCP-CID': CORRELATION_ID,
                          'PTS-LCP-Principal': PRINCIPAL,
                          'Content-Type': 'application/json'
                      },
                      data=json.dumps(data)
                      )
        ])
