# The pShooter API


## Introduction and General Information

This document describes the
[REST](https://en.wikipedia.org/wiki/Representational_state_transfer)
API used to submit tasks to pSshooter, check their status and retrieve
the results.

With exceptions pointed out below, all data in and out of the API is
[JavaScript Object Notation](https://www,json.org) (JSON).

Clients should be prepared to handle being redirected to alternate
locations by the `300` family of HTTP status codes.

HTTPS is the only protocol supported.  Requests made using HTTP will
be rejected.







## Endpoints

### `/` - The Root

| Operation | Description |
|:----------|:----------- |
| `GET`     | Returns a greeting from pShooter including the name of the host as specified in the URL and what the host believes its name to be. |
| `PUT`     | _Not Supported_ |
| `POST`    | _Not Supported_ |
| `DELETE`  | _Not Supported_ |


### `/api` - API Version

| Operation | Description |
|:----------|:----------- |
| `GET`     | Returns the highest API version supported by the service |
| `PUT`     | _Not Supported_ |
| `POST`    | _Not Supported_ |
| `DELETE`  | _Not Supported_ |


### `/hostname` - Host Name

| Operation | Description |
|:----------|:----------- |
| `GET`     | Returns the host's name |
| `PUT`     | _Not Supported_ |
| `POST`    | _Not Supported_ |
| `DELETE`  | _Not Supported_ |


### `/stat/tasks/<state>` - Task State

| Operation | Description |
|:----------|:----------- |
| `GET`     | Returns the number of tasks in the state `<state>`, where `<state>` is one of `pending`, `prep`, `trace`, `running`, `callback`, `finished` or `failed`.   |
| `PUT`     | _Not Supported_ |
| `POST`    | _Not Supported_ |
| `DELETE`  | _Not Supported_ |


### `/tasks` - Tasks

| Operation | Description |
|:----------|:----------- |
| `GET`     | _Not Supported_ |
| `PUT`     | _Not Supported_ |
| `POST`    | Creates a new task and returns its URL as a **non-JSON** string.  See _[Posted Task Format](#posted-task-format)_ for details on the required input data. |
| `DELETE`  | _Not Supported_ |


#### Posted Task Format

Tasks posted to pShooter are a JSON object in this general format:

```
{
    "schema": 1,

    "path": ...,
    "test": { ... },
    "dns": { ... },
    "callback": { ... }
}
```

##### `schema` - Task Schema Version Number

The `schema` indicates what version of the task format is represented
by the rest of the object.  If not provided, the value will be assumed
to be `1` and only features available in that version will be allowed.
Use of features in version `2` (notexistant at this writing) or later
makes this pair required.


##### `path` - Testing Path

The `path` directs the path along which pShooter will do its testing.
It can be provided in one of two forms:

 * **String** - If a string is provided for the path, pShooter will
     perform a pScheduler `trace` test to the IP address provided and
     treat the path found in the result as an array as described
     below.  (For example: `"192.0.2.86"`)

 * **Array** - If an array is provided for the path, each element is a
     string containing an IP address.  If [the test](#the-test)
     specified is single-participant (e.g., `rtt` or `latency`),
     pShooter will run one test between itself and all addresses in
     the array.  For multi-participant tests (e.g., `throughput`),
     pShooter will run tests between itself and all addresses for
     which it can [identify a pScheduler instance associated with the
     address](https://internet2.app.box.com/v/pshooter-dns).  Note
     that pShooter will strip all addresses bound to local interfaces
     from the list before proceeding.  (For example: `[
     "198.51.100.44", "203.0.113.197", "192.0.2.86"]`)


##### `test` - pScheduler Test Specification

The `test` pair is a pScheduler-standard test specification describing
what test pShooter should run between itself and each point along the
path.  Becasue the source and destination ends are variable, pShooter
uses two placeholders, `__A__` and `__Z__`, to signify them and will
replace them in any strings in the test specification.  (Note that
under most circumstances, a source end is not required.)

The JSON for this can be generated using the pScheduler command line
interface's `task` command and `jq`:

```
$ pscheduler task --export throughput --dest __Z__ | jq .test
{
  "spec": {
    "dest": "__Z__",
    "schema": 1
  },
  "type": "throughput"
}
```

For a test to `192.0.2.86`, pShooter will change the specification
shown above to read:

```
...
  "test": {
    "spec": {
      "dest": "192.0.2.86",
      "schema": 1
    },
    "type": "throughput"
  }
...
```


##### `dns` - Augmentation of DNS

If provided, the `dns` object defines additional data for the
[DNS-based scheme](DNS.md) used to identify the nearest pScheduler
node associated with an address.  Augmenting DNS allows allows for
intelligence about networks not participating in the DNS scheme to be
added to the process.  This data is searched prior to DNS, giving it
priority.

The object is a tree starting at the root of DNS and broken down by
labels in the FQDN being resolved.  Like DNS zones, items at any level
in the tree can represent single or multiple labels, so
`gw1.dca.example.net` could be at the top of the tree in its entirety
or split across multiple levels by label (e.g., `gw1` under `dca`
under `example.net`).

Here are three examples, all equivalent:

```
...
# Full FQDNs at the top of the tree

"dns": {
  "17.2.0.192.in-addr.arpa" {
    "PTR": "gw1.dca.example.net"
   },
  "_ipv4._perfsonar.gw1.dca.example.net": {
    "TXT": "{ \"pscheduler\": \"ps.dca.example.net\" }"
  }
}
...
```

```
...
# Split across multiple labels

"dns": {
  "in-addr.arpa": {
    "17.2.0.192" { "PTR": "gw1.dca.example.net" }
  },
  "example.net": {
    "_ipv4._perfsonar.gw1.dca": {
      "TXT": "{ \"pscheduler\": \"ps.dca.example.net\" }"
  }
}
...
```

```
...
# Broken down by individual labels

"dns": {
  "arpa": {
    "in-addr": {
      "192": {
        "0": {
          "2": {
            "17": {
              "PTR": "gw1.dca.example.net"
            }
          }
        }
      }
    }
  },
  "net": {
    "example": {
      "dca": {
        "gw1": {
          "TXT": "{ \"pscheduler\": \"ps.dca.example.net\" }"
        }
      }
    }
  }
}
...
```



##### `callback` - The Callback

If provided, the `callback` directs pShooter to retrieve a URL using
the `GET` method as a way to asynchronously signal that a task has
been completed.  The callback object contains the following pairs:

 * `_href` (String) - The URL to be retrieved.

 * `_params` (Object) - Parameters to be added to the URL as a query
   string.  The value in each pair may be any JSON, but it will be
   converted to a string prior to submission to the server.

 * `_headers` (Object) - Headeds to be added to the request.  The
   value in each pair is a string.

 * `retry-policy` (Array of Objects) - A list describing how to
   attempt retries of the callback should the first one fail.  If not
   provided, pShooter will make one attempt to execute the callback
   before giving up.  Each item in the list is an object containing
   the following:

   * `attempts` (Integer) - The number of times this part of the
     policy is applied.

   * `wait` (String) - The amount of time to wait between attempts asn
     an ISO 8601 duration.


For example:
```
    ...
    "callback": {
        "_href": "https://nms.example.net/callback",
        "_params": {
            "id": "281apple",
            "auth": "oicu812"
        },
        "_headers": {
            "X-Department": "Performing Arts",
            "X-Campus": "east"
        },
        "retry-policy": [
            {"attempts": 2, "wait": "PT5S"},
            {"attempts": 4, "wait": "PT15S"},
            {"attempts": 5, "wait": "PT1M"}
        ]
    }
    ...
```


### `/tasks`_UUID_ - Individual Tasks

| Operation | Description |
|:----------|:----------- |
| `GET`     | Returns the task in its current state as a JSON object.  See _[Retrieved Task Format](#retrieved-task-format)_
for details on the contents of the object. |
| `PUT`     | _Not Supported_ |
| `POST`    | _Not Supported_ |
| `DELETE`  | _(Future Feature)_ Cancels cancels the task if it is still pending and the request was received from the local host or the same one that originally `POST`ed it. |


#### Retreived Task Format

The retrieved task is a JSON object containing the following pairs:

 * diags (String) - Diagnostic information about the completion of the
   task.

 * `eta` (String) - The estimated time of arrival (completion) for the
   task as an ISO 8601 timestamp.  If no time has been estimated, the
   value will be `null`.

 * `hints` (Object) - Information about the initial request for the
   task, containing the following:
    * `requester` (String) - The IP address of the host requesting the
      task.
    * `server` (String) - The IP address on the server where the
      request arrived.

 * `href` (String) - The URL for this object.

 * `path` (Array of Strings) - A list of the addresses of the hops
   along the path.

 * `result` (Array of Objects) - Results of each measurement from the
   first point to each hop in the path that was able to be measured.
   Each result is an object containing the following:

    * `diags` (Array of Strings) - Diagnostic messages from pShooter
      about the test result.  This will usually be empty for
      successful measurements.

    * `hosts` (Object) - Information about the test endpoints, named
      `a` and `z`.  Each pair is an object containing the following:
      * `diags` (String) - Diagnostic information about how the host's
        status as a pScheduler node was discovered.

      * `host` (String) - The host's IP address

      * `pscheduler` (String) - If present, the address of the
        pScheduler node that was used.

      * `schema` (Number) - The version of the host data.  Assume `1` if not
        provided.

    * `href` (String) - The URL of the pScheduler run that made the
      measurement.

    * `participants` (Array of String) - The pScheduler nodes that
      participated in the measurement.

    * `result` (Object) - The result of the measurement in all formats
      pScheduler can provide.  Supplied keys are `application/json`
      for the raw JSON result, `text/html` for HTML and `text/plain`
      for plain text.


 * `spec` (Object) - The specification provided when the task was
   created.  Like pScheduler, pShooter will replace any pair beginning
   with an underscore with `null` to protect potentially-sensitive
   information.

 * `state` (String) - The current state of the task.  This will be one
   of the following values:

    * `pending` - The task has not yet started.
    * `prep` - The task is being prepared to run.
    * `trace` - A trace is being performed.
    * `running` - Measurements are being made.
    * `callback` - The callback, if one was supplied, is being executed.
    * `finished` - The task has been completed.
    * `failed` - The task failed.
    * `canceled` - The task was canceled before it started.

 * `state-display` (String) - Like `state` but in a format suitable for display for humans
