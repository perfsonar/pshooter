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
        self.results["diags"].append(message)
        # TODO: Remove this
        if sys.stderr.isatty():
            sys.stderr.write(message + "\n")


    def __debug(self, message):
        """Add a debug message to the diagnostics"""
        if self.debug:
            self.__diag(message)


    def __init__(
            self,
            test,
            participants,
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

        # Make sure we have sufficient pSchedulers to cover the participants
        if len(participants) == 2 and "pscheduler" not in z:
            # TODO: Assert that Z has a host?
            #self.__diag("No pScheduler for or on %s." % (z["host"]))
            return

        self.results["participants"] = [ a["host"], z["host"] ][0:len(participants)]

        # Fill in the test's blanks and construct a task spec

        test = copy.deepcopy(test)
        test = pscheduler.json_substitute(test, "__A__", a["pscheduler"])
        test = pscheduler.json_substitute(test, "__Z__", z.get("pscheduler", z["host"]))
     
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
            self.__diag("Task: %s" % (task))
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

        # TODO: Use pscheudler.time_until_seconds()
        sleep_seconds = (sleep_time.days * 86400) \
                        + (sleep_time.seconds) \
                        + (sleep_time.microseconds / (10.0**6)) \
                        + 5

        self.__debug("Sleeping %f seconds" % (sleep_seconds))
        time.sleep(sleep_seconds)

        result_href = self.run_data["result-href"]
        # TODO: Do a fetch/wait on the result


        # Fetch the results in all formats we return.

        # TODO: Need to handle run failures


        self.results["results"] = {}


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



    runner = TaskRunner(test, participants, a, z, debug=True)
    result = runner.result()
    print pscheduler.json_dump(result, pretty=True)
