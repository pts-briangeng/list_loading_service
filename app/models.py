class Request(object):

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.file = kwargs.get('file', '')
        self.index = kwargs.get('index', '')
        self.type = kwargs.get('type', '')
        self.callbackUrl = kwargs.get('callbackUrl', '')
