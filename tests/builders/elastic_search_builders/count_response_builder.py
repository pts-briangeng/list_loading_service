import copy
import httplib

from tests.builders import base

COUNT_LIST_ERROR_RESPONSE = {
    "error": "IndexMissingException[[offers] missing]",
    "status": 404
}

COUNT_LIST_ZERO_RESPONSE = {
    "count": 0
}

HTTP_RESPONSE = {
    "status_code": httplib.OK,
    "Content-Type": "application/json",
    "Content-Length": 111,
    "response": {}
}


class CountListResponseJsonBuilder(base.BaseBuilder):
    def __init__(self):
        super(CountListResponseJsonBuilder, self).__init__()

    def with_count_zero(self):
        list_status_response = copy.deepcopy(COUNT_LIST_ZERO_RESPONSE)
        self.collection.append(list_status_response)
        return self

    def with_error_response(self):
        list_status_response = copy.deepcopy(COUNT_LIST_ERROR_RESPONSE)
        self.collection.append(list_status_response)
        return self

    def build(self, with_errors):
        return self.collection

    def http_response(self):
        http_response = copy.deepcopy(HTTP_RESPONSE)
        http_response['response'] = self.collection.singleton()
        return http_response
