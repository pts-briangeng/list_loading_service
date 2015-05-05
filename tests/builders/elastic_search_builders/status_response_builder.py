import copy
import httplib

from tests.builders import base


LIST_STATUS_RESPONSE = {
    "_shards": {
        "failed": 0,
        "successful": 5,
        "total": 5
    },
    "hits": {
        "hits": [],
        "max_score": 0.0,
        "total": "@int(total_count)"
    },
    "links": {
        "self": {
            "href": "http://localhost:5000/index/offers/type/edaa3541-7376-4eb3-8047-aaf78af900da/status"
        }
    },
    "timed_out": False,
    "took": 1
}

HTTP_RESPONSE = {
    "status_code": httplib.OK,
    "Content-Type": "application/json",
    "Content-Length": 111,
    "response": {}
}


class ListStatusResponseJsonBuilder(base.BaseBuilder):
    def __init__(self, **data):
        self.list_status_response = base.mock_json(copy.deepcopy(LIST_STATUS_RESPONSE), **data)

    def build(self):
        return self.list_status_response

    def http_response(self):
        http_response = copy.deepcopy(HTTP_RESPONSE)
        http_response['response'] = self.build()
        return http_response
