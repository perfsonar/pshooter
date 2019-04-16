"""
Task Runner Class for pShooter
"""

import copy
import datetime
import dateutil.parser
import pscheduler
import sys
import threading
import time

from dateutil.tz import tzlocal


class TaskRunner(object):
    """
    Task Runner
    """

    def __debug(self, message):
        """Log a debug message"""
        self.log.debug("%s: %s: %s" % (self.task, self.z["host"], message))


    def __diag(self, message):
        """Add a message to the diagnostics"""
        self.results["diags"].append(message)
        self.__debug(message)



    def __init__(
            self,
            test,
            participants,
            a,
            z,
            log,
            task,
            requester,
            auth_name,
            auth_key
            ):
        """
        Construct a task runner
        """

        self.test = test
        self.participants = participants
        self.a = a
        self.z = z
        self.log = log
        self.task = task

        self.results = {
            "hosts": {
                "a": a,
                "z": z
            },
            "diags": []
        }

        """This runs the process."""
        # Make sure we have sufficient pSchedulers to cover the participants
        if len(self.participants) == 2 and "pscheduler" not in self.z:
            self.__diag("No pScheduler for or on %s." % (self.z["host"]))
            return

        self.results["participants"] = [ self.a["host"], self.z["host"] ][0:len(self.participants)]

        # Fill in the test's blanks and construct a task spec

        a_end = self.a["pscheduler"]
        z_end = self.z.get("pscheduler", self.z["host"])
        test = copy.deepcopy(self.test)
        test = pscheduler.json_substitute(test, "__A__", a_end)
        test = pscheduler.json_substitute(test, "__Z__", z_end)
     
        task = {
            "schema": 1,
            "test": test,
            # This is required; empty is fine.
            "schedule": {
                # TODO: Don't hard-wire this.
                "slip": "PT10M"
            }
        }

        # Post the task

        self.__debug("Posting task %s -> %s" % (a_end, z_end))
        task_post = pscheduler.api_url(host=a_end, path="/tasks")

        requester_header = "%s;%s;%s" % (requester, auth_name, auth_key)
        

        status, task_url = pscheduler.url_post(task_post,
                                               data=pscheduler.json_dump(task),
                                               headers={
                                                   "X-pScheduler-Requester": requester_header
                                               },
                                               throw=False)
        if status != 200:
            self.__diag("Task: %s" % (self.task))
            self.__diag("Unable to post task: %s" % (task_url))
            return

        self.__debug("Posted task %s" % (task_url))

        # Get the task from the server with full details

        status, task_data = pscheduler.url_get(task_url,
                                               params={"detail": True},
                                               throw=False)
        if status != 200:
            self.__diag("Unable to get detailed task data: %s" % (task_data))
            return

        # Wait for the first run to be scheduled

        first_run_url = task_data["detail"]["first-run-href"]

        status, run_data = pscheduler.url_get(first_run_url, throw=False)

        if status == 404:
            self.__diag("The server never scheduled a run for the task.")
            return
        if status != 200:
            self.__diag("Error %d: %s" % (status, run_data))
            return
                
        for key in ["start-time", "end-time", "result-href"]:
            if key not in run_data:
                self.__diag("Server did not return %s with run data" % (key))
                return

        self.results["href"] = run_data["href"]
        self.run_data = run_data
        self.__debug(
            "Run times: %s to %s" \
            % (run_data["start-time"], run_data["end-time"]))

        self.worker = threading.Thread(target=lambda: self.run())
        self.worker.setDaemon(True)
        self.worker.start()


    def __run(self):

        # Wait for the run time to have passed

        try:
            # The end time comes back as ISO 8601.  Parse it.
            end_time = dateutil.parser.parse(self.run_data["end-time"])
        except ValueError as ex:
            self.__diag("Server did not return a valid end time for the task: %s" % (str(ex)))
            return

        # Wait for the task to run.  The extra time added is a
        # breather for the server to assemble the final result.

        if end_time >= pscheduler.time_now():
            sleep_time = pscheduler.time_until_seconds(end_time) + 3
            self.__debug("Sleeping %f seconds" % (sleep_time))
            time.sleep(sleep_time)

        # Fetch the run, waiting for the result

        result_href = self.run_data["result-href"]

        self.__debug("Waiting for result to be ready")
        status, run = pscheduler.url_get(
            self.run_data["href"],
            params={ 'wait-merged': True },
            throw=False)

        if status != 200:
            self.__diag("Failed to fetch run for result: %d: %s" % (status, run))
            return

        # Fetch the results in all formats we return.

        self.results["results"] = {}


        for fmt in [ "application/json", "text/plain", "text/html" ]:
            self.__debug("Fetching %s" % (fmt))
            status, result = pscheduler.url_get(
                result_href,
                params={ "wait-merged": True, "format": fmt },
                json=fmt == "application/json",
                throw=False
            )
            if status != 200:
                self.__diag("Failed to get %s result: %s" % (fmt, result))
                return

            if fmt == "application/json" and not result.get("succeeded", False):
                self.__diag("Task failed.")
                return

            self.results["results"][fmt] = result




    def run(self):
        self.__debug("Worker started")
        try:
            self.__run()
        except Exception as ex:
            self.__diag(str(ex))
        self.__debug("Worker finished")


    def result(self):
        """Wait for the result and return it."""

        try:
            if self.worker.is_alive():
                self.worker.join()
        except AttributeError:
            pass  # Don't care if it's not there.    
        
        return self.results



if __name__ == "__main__":

    test = {
        "type": "trace",
        "spec": {
            "schema": 1,
            "dest": "__Z__"
        }
    }

    a = {
        "pscheduler": "dev1",
        "host": "dev1"
    }

    # This is okay for the other end if it's a one-participant test
    z = {
        "pscheduler": "www.perfsonar.net",
        "host": "www.perfsonar.net"
    }

    participants = [ "dev1" ]



    runner = TaskRunner(test, participants, a, z)
    result = runner.result()
    print pscheduler.json_dump(result, pretty=True)
