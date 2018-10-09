#
# Administrative Information
#

import datetime
import pscheduler
import pytz
import socket
import tzlocal

from pshooterapiserver import application

from .access import *
from .args import arg_integer
from .dbcursor import dbcursor_query
from .response import *
from .util import *
from .log import log

@application.route("/", methods=['GET'])
def root():
    return ok_json("This is the pShooter API server on %s (%s)."
              % (server_hostname(), pscheduler.api_local_host_fqdn()))



max_api = 1


@application.route("/api", methods=['GET'])
def api():
    return ok_json(max_api)


@application.before_request
def before_req():
    log.debug("REQUEST: %s %s", request.method, request.url)

    try:
        version = arg_integer("api")
        if version is None:
            version = 1
        if version > max_api:
            return not_implemented(
                "No API above %s is supported" % (max_api))
    except ValueError:
        return bad_request("Invalid API value.")

    # All went well.
    return None


@application.errorhandler(Exception)
def exception_handler(ex):
    log.exception()
    return error("Internal problem; see system logs.")


@application.route("/exception", methods=['GET'])
def exception():
    """Throw an exception"""
    # Allow only from localhost
    if not request.remote_addr in ['127.0.0.1', '::1']:
        return not_allowed()

    raise Exception("Forced exception.")


@application.route("/hostname", methods=['GET'])
def hostname():
    """Return the hosts's name"""
    return ok_json(pscheduler.api_local_host_fqdn())
