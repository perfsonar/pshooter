#!/usr/bin/python

import copy
import ipaddress
import sys

from parallelrun import *
from taskrunner import *


def _pscheduler_at(host, diags=None):

    (has_ps, reason) = pscheduler.api_ping(host)

    diag_list = []
    if diags is not None:
        diag_list.append(diags)

    result = {
        "schema": 1,
        "host": host
    }
    if has_ps:
        result["pscheduler"] = host
        diag_list.append("Found pScheduler on host directly.")
    else:
        diag_list.append(reason)

    result["diags"] = ";  ".join(diag_list)

    return result



def _resolve_from_family(family_record_type, hostname, resolver, api_check):

    # Try to resolve family-specific and non-family-specific records.

    for record_type in [ family_record_type, None ]:

        ps_fqdn = "{0}_perfsonar.{1}".format(
            "" if record_type is None else "_ipv{0}.".format(record_type),
            hostname
        )

        txt = resolver(ps_fqdn, "TXT")

        # If there's no TXT record, then see if pScheduler is running
        # on the original host as a last-ditch effort.  This doesn't
        # do much for most hosts along a route but might help catch
        # perfSONAR nodes at the very end, enabling two-participant
        # tests.

        if txt is None:
            return _pscheduler_at(hostname, "No TXT record for %s" % (ps_fqdn))

        txt_json = None
        redirects = 0

        while redirects < 5:

            try:
                txt_json = pscheduler.json_load(txt)
            except ValueError:
                # If it doesn't look like JSON, do another last-ditch
                # attempt at the address.
                return _pscheduler_at(hostname, "TXT record for %s contains invalid JSON" % (ps_fqdn))

            if "href" not in txt_json:
                # No href means we have the final version
                break

            # Handle a redirect

            redirects += 1
            try:
                (status, txt_json) = pscheduler.url_get(txt_json["href"], throw=False)
            except ValueError:
                status = 0
            if status != 200:
                # Nothing else we can do.
                return _pscheduler_at(hostname, "Failed to fetch %s: %d: %s" % (txt_json["href"], status, txt_json))

            break

        if "href" in txt_json:
            # Too many redirects.  Last-ditch it.
            return _pscheduler_at(hostname, "Too many redirects for %s" % (ps_fqdn))

        txt_json["host"] = hostname

        if api_check and "pscheduler" in txt_json:

            (has_ps, reason) = pscheduler.api_ping(txt_json["pscheduler"])
            if has_ps:
                return txt_json
            else:
                return _pscheduler_at(hostname, "%s: %s" % (txt_json["pscheduler"], reason))

        return txt_json



def _resolve_pscheduler_node(args):

    """
    Find the pScheduler information for a host
    """

    (host, resolver, api_check) = args

    if not isinstance(host, unicode):
        host = unicode(host, "utf-8")
    addr = ipaddress.ip_address(host)

    if isinstance(addr, ipaddress.IPv4Address):
        family_record_type = "4"
    elif isinstance(addr, ipaddress.IPv6Address):
        family_record_type = "6"
    else:
        raise ValueError("Address %s is not IPv4 or IPv6" % (host))

    assert isinstance(api_check, bool), "Invalid api_check; must be boolean."


    # Reverse-resolve the address

    fqdn = resolver(addr.reverse_pointer, "PTR")
    if fqdn is None:
        # There's no reverse mapping, try for pScheduler on the host
        # directly as a last resort.
        return _pscheduler_at(host, "No PTR record for %s" % (host))

    # Go through ever-shorter versions of the FQDN until something resolves.

    ps_host_parts = fqdn.split(".")

    while ps_host_parts and ps_host_parts[0]:
        search = ".".join(ps_host_parts)
        #print "Searching", search
        resolve_result = _resolve_from_family(
            family_record_type, search, resolver, api_check
        )

        if "pscheduler" in resolve_result:
            #print "FOUND: ", resolve_result
            # The returned host may be chopped
            resolve_result["host"] = fqdn
            return resolve_result

        del ps_host_parts[0]

    # Nothing resolved means nothing found.

    return {
        "schema": 1,
        "diags": "No pScheduler found",
        "host": fqdn
    }






def run_test( data, resolver, log, task):

    # Identify pScheduler nodes for all hops

    self.hops = data["path"]

    if len(self.hops) < 2:
        raise ValueError("Path must have at least two hops.")

    args = [ (host, resolver, False) for host in hops ]
    nodes = parallel_run(_resolve_pscheduler_node, args)

    a = nodes.pop(0)


    if "pscheduler" not in a:
        raise ValueError("First hop must have perfSONAR: %s"
                         % (a.get("diags", "Unknown error")))


    # Assemble a list of the tests to run.
    # (Test Spec, A, Z, Error Message)

    # If the test spec is None, the test is considered un-runnable for
    # the reason in the error message.

    tests = []


    # Assemble a prototype of the test to be run and ask the first hop
    # (which will be the lead on all of the tests) whether or not the
    # test is valid and for a participant list.  Note that the
    # underscores aren't valid hostnames for DNS.

    prototype = copy.copy(data["test"])
    # Don't use IPs here since you can't assume what stack(s) a host
    # will be running.
    prototype = pscheduler.json_substitute(prototype, "_A_", "localhost")
    prototype = pscheduler.json_substitute(prototype, "_Z_", "localhost")

    prototype_spec_text = pscheduler.json_dump(prototype["spec"])


    # If there's a port tagged onto the host, split it out before
    # formatting the URL.

    a_parts = a["pscheduler"].split(":")
    if len(a_parts) == 1:
        a_parts.append(None)

    test_url = pscheduler.api_url(
        host=a_parts[0],
        port=a_parts[1],
        path="/tests/%s" % (prototype["type"]))

    # Validate the spec

    (status, is_valid) = pscheduler.url_get(
        test_url + "/spec/is-valid",
        params={ "spec": prototype_spec_text },
        throw=False
        )

    if status == 404:
        raise ValueError("Can't find test %s on %s"
                         % (prototype["type"], a["pscheduler"]))

    if status != 200:
        raise ValueError("Unable to validate spec: %s" % (is_valid))

    if not is_valid["valid"]:
        raise ValueError("Spec is not valid: %s"
                         % (is_valid.get("error", "Unspecified error")))

    # Get the participants

    (status, participants) = pscheduler.url_get(
        test_url + "/participants",
        params={ "spec": prototype_spec_text },
        throw=False
        )

    if status != 200:
        raise RuntimeError("Unable to fetch participants: %s" % (participants))
    log.debug("%d: Participants: %s", task, participants["participants"])

    runners = []

    for z in nodes:
        runners.append(TaskRunner(data["test"],
                                  participants["participants"],
                                  a, z,
                                  log, task))
        log.debug("%s: Started task to %s", task, z["host"])

    results = []
    for runner in runners:
        result = runner.result()
        results.append(result)

    return results
