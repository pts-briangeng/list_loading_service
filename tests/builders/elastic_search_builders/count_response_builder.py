import copy
import httplib

from tests.builders import base

COUNT_LIST_ERROR_RESPONSE = {
    "error": "IndexMissingException[[offers] missing]",
    "status": 404
}

HTTP_RESPONSE = {
    "status_code": httplib.OK,
    "Content-Type": "application/json",
    "Content-Length": 111,
    "response": {}
}


class CountListResponseJsonBuilder(base.BaseBuilder):
    def with_count(self, count=0):
        list_status_response = copy.deepcopy({
            "count": count
        })
        self.collection.append(list_status_response)
        return self

    def with_error_response(self):
        list_status_response = copy.deepcopy(COUNT_LIST_ERROR_RESPONSE)
        self.collection.append(list_status_response)
        return self

    def build(self):
        return self.collection

    def http_response(self):
        http_response = copy.deepcopy(HTTP_RESPONSE)
        http_response['response'] = self.collection.singleton()
        return http_response
