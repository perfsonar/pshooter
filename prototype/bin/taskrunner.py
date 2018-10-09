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

    def __diag(self, message):
        """Add a message to the diagnostics"""
        self.diags.append(message)
        if sys.stderr.isatty():
            sys.stderr.write(message + "\n")


    def __debug(self, message):
        """Add a debug message to the diagnostics"""
        if self.debug:
            self.__diag(message)


    def __init__(
            self,
            test,
            nparticipants,
            a,
            z,
            debug=False
            ):
        """
        Construct a task runner
        """

        self.debug = debug

        self.results = {
            "hosts": {
                "a": a,
                "z": z
            },
            "diags": []
        }
        self.diags = self.results["diags"]

        # Make sure we have sufficient pSchedulers to cover the participants
        if (nparticipants == 2) and ("pscheduler" not in z):
            # TODO: Assert that Z has a host?
            self.__diag("No pScheduler for or on %s." % (z["host"]))
            return


        # Fill in the test's blanks and construct a task spec

        test = copy.deepcopy(test)
        test = pscheduler.json_substitute(test, "__A__", a["pscheduler"])

        z_end = z["host"] if nparticipants == 1 else z.get("pscheduler", z["host"])
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

        task_post = pscheduler.api_url(host=a["pscheduler"], path="/tasks")

        status, task_url = pscheduler.url_post(task_post,
                                               data=pscheduler.json_dump(task),
                                               throw=False)
        if status != 200:
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
        """This runs the process."""

        # Wait for the run time to have passed

        try:
            # The end time comes back as ISO 8601.  Parse it.
            end_time = dateutil.parser.parse(self.run_data["end-time"])
        except ValueError as ex:
            self.__diag("Server did not return a valid end time for the task: %s" % (str(ex)))

        now = datetime.datetime.now(tzlocal())
        sleep_time = end_time - now if end_time > now else datetime.timedelta()

        # The extra five seconds is a breather for the server to 
        # assemble the final result.
        sleep_seconds = (sleep_time.days * 86400) \
                        + (sleep_time.seconds) \
                        + (sleep_time.microseconds / (10.0**6)) \
                        + 5

        self.__debug("Sleeping %f seconds" % (sleep_seconds))
        time.sleep(sleep_seconds)

        # Fetch the results in all formats we return.

        # TODO: Need to handle run failures

        self.results["results"] = {}

        result_href = self.run_data["result-href"]
        for fmt in [ "application/json", "text/plain", "text/html" ]:
            status, result = pscheduler.url_get(
                result_href,
                params={ "wait-merged": True, "format": fmt },
                json=fmt == "application/json",
                throw=False
            )
            if status != 200:
                self.__diag("Failed to get %s result: %s" % (fmt, result))
                return

            self.results["results"][fmt] = result




    def run(self):
        self.__debug("Worker started")
        try:
            self.__run()
        except Exception as ex:
            self.__diag(str(ex))


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
        "type": "simplestream",
        "spec": {
            "schema": 1,
            "dest": "__Z__"
        }
    }

    a = {
        "pscheduler": "dev7",
        "host": "dev7"
    }

    z = {
        "pscheduler": "dev6",
        "host": "dev6"
    }

    nparticipants = 2



    r = TaskRunner(test, nparticipants, a, z, debug=True)
    print pscheduler.json_dump(r.result(), pretty=True)
