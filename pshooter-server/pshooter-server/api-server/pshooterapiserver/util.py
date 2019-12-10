#
# Utility Functions
#

import socket
import urlparse
import uuid

from flask import request

from dbcursor import *


#
# Hints
#

def request_hints():
    result = {
        "requester": request.remote_addr
    }

    # This handles things cross-platform with Apache first.
    for var in [ "SERVER_ADDR", "LOCAL_ADDR" ]:
        value = request.environ.get(var, None)
        if value is not None:
            result["server"] = value
            break

    return result



#
# Hostnames
#

def server_hostname():
    """
    Figure out the name of the server end of the request, punting if it's
    the local host or not available.
    """

    return urlparse.urlparse(request.url_root).hostname


def server_netloc():
    """
    Figure out the netloc of the server end of the request, punting if it's
    the local host or not available.
    """

    return urlparse.urlparse(request.url_root).netloc



#
# UUIDs
#

def uuid_is_valid(test_uuid):
    """
    Determine if a UUID is valid
    """
    try:
        uuid_object = uuid.UUID(test_uuid)
    except ValueError:
        return False
    return True
