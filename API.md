# The pShooter API


## Introduction and General Information

This document describes the REST API used to submit tasks to
pSshooter, check their status and retrieve the results.

HTTPS is the only protocol supported.  Requests made using HTTP will
be rejected.

With exceptions pointed out below, all data in and out of the API is
[JavaScript Object Notation](https://www,json.org) (JSON).

Clients should be prepared to handle being redirected to alternate
locations by the `300` family of HTTP status codes.




## Adminstrative endpoints

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

**TODO: Write this**


##### The Callback

**TODO: Write this**

```
    ...
    "callback": {
        "_href": "https://nms.example.net/callback",
        "_params": {
            "id": "572034",
            "auth": "70487ec5-666e-46f0-91ea-dfeedf5bd24f"
        },
        "_headers": {
            "#X!Bad!Header": "bad",
            "X-Fake-Parameter": "gobsmacked",
            "X-Faker-Parameter": "gobsmackeder"
        },
        "retry-policy": [
            {"attempts": 2, "wait": "PT5S"},
            {"attempts": 4, "wait": "PT15S"},
            {"attempts": 5, "wait": "PT1M"}
        ]
    }
    ...
```














------------------------------------------------------------
OLD
------------------------------------------------------------



`/tasks/`_UUID_ - `GET` returns the task in its current state as a
JSON object.  See _[Retrieved Task Format](#retrieved-task-format)_
for details on the contents of the object.  Once implemented, `DELETE`
cancels the task if it is still pending and the request was received
from the local host or the same one that originally `POST`ed it.






## Retreived Task Format

**TODO: Write this**
