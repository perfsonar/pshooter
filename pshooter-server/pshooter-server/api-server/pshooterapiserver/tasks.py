#
# Task-Related Pages
#

import pscheduler
import urlparse

from pshooterapiserver import application

from flask import request

from .access import *
from .dbcursor import dbcursor_query
from .json import *
from .log import log
from .response import *
from .util import *


class TaskPostingException(Exception):
    """This is used internally when some phase of task posting fails."""
    pass


def task_exists(task):
    """Determine if a task exists by its UUID"""

    cursor = dbcursor_query("SELECT EXISTS (SELECT * FROM task WHERE uuid = %s)",
                            [task], onerow=True)

    return cursor.fetchone()[0]
    

__TASK_SCHEMA = {

    "local": {
        "dns": {
            "type": "object",
            "patternProperties": {
                "^[A-Za-z0-9-_]+(\.[A-Za-z0-9-_]*)*$": {
                    "oneOf": [
                        { "$ref": "#/pScheduler/String" },
                        { "$ref": "#/local/dns" }
                    ]
                }
            },
            "additionalProperties": False
        },
    },

    "type": "object",
    "properties": {

        "schema": {
            "type": "integer",
            "enum": [ 1 ]
        },
                
        "path": {
            "oneOf": [
                { "$ref": "#/pScheduler/IPAddress" },
                { "type": "array", "items": { "$ref": "#/pScheduler/IPv4" } },
                { "type": "array", "items": { "$ref": "#/pScheduler/IPv6" } }
            ]
        },

        "test": { "$ref": "#/pScheduler/TestSpecification" },

        "dns": { "$ref": "#/local/dns" },

        # TODO: This should probably become part of the
        # pScheduler library since it will be useful
        # elsewhere.

        "callback": {
            "type": "object",
            "properties": {
                "_href": {"$ref": "#/pScheduler/URL"},
                "_params": {
                    "type": "object",
                    "patternProperties": {
                        "^.*$": { "$ref": "#/pScheduler/AnyJSON" }
                    },
                    "additionalProperties": False
                },
                "_headers": {
                    "type": "object",
                    "patternProperties": {
                        "^[\w-]+$": { "$ref": "#/pScheduler/String" }
                    },
                    "additionalProperties": False
                },
                "bind": { "$ref": "#/pScheduler/Host" },
                "retry-policy": {
                    "type": "array",
                    "items": {"$ref": "#/pScheduler/RetryPolicyEntry"}
                }
            },
            "required": [ "_href" ],
            "additionalProperties": False
        }
    },
    "required": ["path", "test"],
    "additionalProperties": False
}



@application.route("/tasks", methods=['POST'])
def tasks():

    try:
        task = pscheduler.json_load(request.data, max_schema=1)
    except ValueError as ex:
        return bad_request("Invalid task specification: %s" % (str(ex)))

    valid, message = pscheduler.json_validate(task, __TASK_SCHEMA)

    if not valid:
        return bad_request("Invalid task specification: %s" % (message))

    # TODO: Need to get and stash the actual requester so the service
    # can do a proxied request and pScheduler can enforce its limits.

    cursor = dbcursor_query(
            "SELECT * FROM api_task_post(%s)",
            [ pscheduler.json_dump(task) ])

    if cursor.rowcount == 0:
        return error("Task post failed; API returned nothing.")

    task_uuid = cursor.fetchone()[0]
    log.debug("New task UUID %s", task_uuid)

    task_url = "%s/%s" % (request.base_url, task_uuid)

    return ok(task_url)



@application.route("/tasks/<uuid>", methods=['GET', 'DELETE'])
def tasks_uuid(uuid):

    if not uuid_is_valid(uuid):
        return not_found()

    if request.method == 'GET':

        return json_query("SELECT fullrec FROM task WHERE uuid = %s",
                          [uuid], single=True)

    elif request.method == 'DELETE':

        # TODO: Do this
        return not_implemented()
