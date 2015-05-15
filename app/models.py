class Request(object):

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.filePath = kwargs.get('filePath', '')
        self.service = kwargs.get('service', '')
        self.list_id = kwargs.get('list_id', '')
        self.member_id = kwargs.get('member_id', '')
        self.callbackUrl = kwargs.get('callbackUrl', '')
