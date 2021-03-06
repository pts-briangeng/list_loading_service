import copy
import httplib

from tests.builders import base

DELETE_LIST_OK_RESPONSE = {
  "_indices": {
    "offers": {
      "_shards": {
        "total": 5,
        "successful": 5,
        "failed": 0
      }
    }
  }
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

    def with_ok_response(self):
        list_status_response = copy.deepcopy(DELETE_LIST_OK_RESPONSE)
        self.collection.append(list_status_response)
        return self

    def with_error_response(self):
        list_status_response = copy.deepcopy(DELETE_LIST_ERROR_RESPONSE)
        self.collection.append(list_status_response)
        return self

    def build(self, with_errors):
        return self.collection

    def http_response(self):
        http_response = copy.deepcopy(HTTP_RESPONSE)
        http_response['response'] = self.collection.singleton()
        return http_response
