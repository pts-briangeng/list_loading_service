import httplib


def Any(cls):
    class Any(object):

        def __eq__(self, other):
            return type(other) == cls

    return Any()


def generator(data):
    yield data


class MockHttpResponse(object):

    def __init__(self, status_code=httplib.OK, response=None):
        self.status_code = status_code
        self.response = response

    def json(self):
        return self.response

    def status_code(self):
        return self.status_code

    def raise_for_status(self):
        if self.status_code not in [httplib.OK, httplib.CREATED]:
            raise Exception
