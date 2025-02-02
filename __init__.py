# -*- coding: utf-8 -*-

import logging

__version__ = '1.2u'

logger = logging.getLogger('uPHue')


def is_string(data):
    """Utility method to see if data is a string."""
    return isinstance(data, str)


class PhueException(Exception):

    def __init__(self, id, message):
        self.id = id
        self.message = message


class PhueRegistrationException(PhueException):
    pass


class PhueRequestTimeout(PhueException):
    pass
