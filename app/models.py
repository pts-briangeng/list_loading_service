class Request(object):

    def __init__(self, **kwargs):
        self.url = kwargs.get('url', '')
        self.file = kwargs.get('file', '')
        self.service = kwargs.get('service', '')
        self.listId = kwargs.get('list_id', '')
        self.memberId = kwargs.get('member_id', '')
        self.callbackUrl = kwargs.get('callbackUrl', '')
