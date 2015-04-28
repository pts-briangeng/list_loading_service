import copy
import httplib

import base

RESPONSE = {}

HTTP_RESPONSE = {
    "status_code": httplib.OK,
    "Content-Type": "application/json",
    "Content-Length": len(RESPONSE),
    "response": RESPONSE
}


class ElasticSearchResponseJsonBuilder(base.BaseBuilder):

    def _init_(self):
        super(ElasticSearchResponseJsonBuilder, self).__init__()

    def with_items(self, **data):
        response = base.mock_json(copy.deepcopy(RESPONSE), **data)
        response['items'] = []
        response = {
            "status_code": httplib.OK,
            "Content-Type": "application/json",
            "Content-Length": len(RESPONSE),
            "response": {'items': []}
        }
        self.collection.append(response)
        return self.collection

    def build(self, **data):
        self.collection.append(base.mock_json(copy.deepcopy(HTTP_RESPONSE), **data))
        return self.collection
