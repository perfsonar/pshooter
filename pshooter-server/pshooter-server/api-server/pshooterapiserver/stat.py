#
# Statistics-Related Pages
#

import pscheduler

from pshooterapiserver import application

from flask import request

from .dbcursor import dbcursor_query
from .json import *
from .response import *


def single_numeric_query(query, query_args=[]):

    cursor = dbcursor_query(query, query_args)

    if cursor.rowcount == 0:
        return not_found()

    row = cursor.fetchone()
    cursor.close()

    return ok(str(row[0]))



#
# Tasks
#

@application.route("/stat/tasks/<state>", methods=['GET'])
def stat_tasks_state(state):

    # TODO: Query the database for this
    if state not in [ "pending", "prep", "trace", "running",
                      "callback", "finished", "failed" ]:
        return not_found()

    return single_numeric_query("SELECT COUNT(*) FROM task WHERE STATE = task_state_%s()" \
                                % (state))
