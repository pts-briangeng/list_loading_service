class Request(object):

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.file = kwargs.get('file', '')
        self.service = kwargs.get('service', '')
        self.id = kwargs.get('id', '')
        self.callbackUrl = kwargs.get('callbackUrl', '')
