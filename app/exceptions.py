import httplib

from restframework import errors


EXCEPTION_TRANSLATIONS = {
    Exception: (httplib.INTERNAL_SERVER_ERROR,
                errors.INTERNAL_SERVER_ERROR, 'Internal server error.'),
    LookupError: (httplib.NOT_FOUND,
                  errors.NOT_FOUND, None)}
