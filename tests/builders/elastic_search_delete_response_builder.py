import copy
import httplib

import base


DELETE_LIST_OK_RESPONSE = {
    "acknowledged": True
}

DELETE_LIST_ERROR_RESPONSE = {
    "error": "TypeMissingException[[_all] type[[test]] missing: No index has the type.]",
    "status": 404
}

HTTP_RESPONSE = {
    "status_code": httplib.OK,
    "Content-Type": "application/json",
    "Content-Length": 111,
    "response": {}
}


class DeleteListResponseJsonBuilder(base.BaseBuilder):
    def __init__(self):
        self.list_status_response = copy.deepcopy(DELETE_LIST_OK_RESPONSE)

    def with_response(self):
        self.list_status_response = copy.deepcopy(DELETE_LIST_OK_RESPONSE)
        return self

    def with_error_response(self):
        self.list_status_response = copy.deepcopy(DELETE_LIST_ERROR_RESPONSE)
        return self

    def build(self, with_errors):
        if with_errors:
            return copy.deepcopy(DELETE_LIST_ERROR_RESPONSE)
        return self.list_status_response

    def http_response(self, with_errors=False):
        http_response = copy.deepcopy(HTTP_RESPONSE)
        http_response['response'] = self.build(with_errors)
        return http_response
