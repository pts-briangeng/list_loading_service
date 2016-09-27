import httplib

from restframework import errors


class TooManyAccountsSpecifiedError(Exception):

    """ There are too many accounts specified. """
    pass


EXCEPTION_TRANSLATIONS = {
    TooManyAccountsSpecifiedError: (httplib.BAD_REQUEST,
                                    errors.BAD_REQUEST, 'There are too many accounts specified.'),
    Exception: (httplib.INTERNAL_SERVER_ERROR,
                errors.INTERNAL_SERVER_ERROR, 'Internal server error.'),
    LookupError: (httplib.NOT_FOUND,
                  errors.NOT_FOUND, None)}
