import httplib

from restframework import errors


class FileTooBigError(Exception):

    """ There are too many lists currently being processed. """
    pass


EXCEPTION_TRANSLATIONS = {
    FileTooBigError: (httplib.BAD_REQUEST,
                      errors.BAD_REQUEST, 'There are too many lists currently being processed.'),
    Exception: (httplib.INTERNAL_SERVER_ERROR,
                errors.INTERNAL_SERVER_ERROR, 'Internal server error.'),
    LookupError: (httplib.NOT_FOUND,
                  errors.NOT_FOUND, None)}
