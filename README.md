
# pShooter

pShooter is a tool that automates part of the process of troubleshooting network problems between two points by running pScheduler tests to as many perfSONAR nodes as can be found along the path between them.  It consists of a web service with a [REST API](#the-api) and a [scheme for placing information into the Domain Name Service](https://internet2.app.box.com/v/pshooter-dns) that can be used to locate perfSONAR nodes in close proximity to the path.

A full description and a demonstration of a prototype version of
pShooter can be found [on
YouTube](https://www.youtube.com/watch?v=2HUY6b5T9DM).


## The API

The pShooter REST API consists of the five endpoints below.

`/api` - `GET` returns the API version supported by the server as an integer.

`/hostname` - `GET` returns the host's name as a string.

`/stat/tasks/`_state_ - `GET` returns the number of tasks in the `<state>` state as an integer, where _state_ is one of `pending`, `prep`, `trace`, `running`, `callback`, `finished` or `failed`.

`/tasks` - `POST` creates a new task and returns its URL as a non-JSON string (i.e., unquoted).  See _[Posted Task Format](#posted-task-format)_ for details on the required input.

`/tasks/`_UUID_ - `GET` returns the task in its current state as a JSON object.  See _[Retrieved Task Format](#retrieved-task-format)_ for details on the contents of the object.  `DELETE` cancels the task if it is still pending and the request was received from the local host or the same one that originally `POST`ed it.


## Posted Task Format

pShooter is tasked with an HTTP `POST` to the `/pshooter/tasks` endpoint.

```
{
    "schema": 1,

    "path": ...,
    "test": { ... },
    "dns": { ... },
    "callback": { ... }
}
```

### The Path

The network path to be tested can be provided in one of two forms:

**String** - If a string is provided for the path, pShooter will perform a pScheduler `trace` test to the IP address provided and treat the path found in the result as an array as described below.  (For example: `"192.0.2.86"`)

**Array** - If an array is provided for the path, each element is a string containing an IP address.  If [the test](#the-test) specified is single-participant (e.g., `rtt` or `latency`), pShooter will run one test between itself and all addresses in the array.  For multi-participant tests (e.g., `throughput`), pShooter will run tests between itself and all addresses for which it can [identify a pScheduler instance associated with the address](https://internet2.app.box.com/v/pshooter-dns).  Note that pShooter will strip all addresses bound to local interfaces from the list before proceeding.  (For example: `[ "198.51.100.44", "203.0.113.197", "192.0.2.86"]`)


### The Test

The `test` pair is a pScheduler-standard test specification describing what test pShooter should run between itself and each point along the path.  Becasue the source and destination ends are variable, pShooter uses two placeholders, `__A__` and `__Z__`, to signify them and will replace them in any strings  in the test specification.  (Note that under most circumstances, a source end is not required.)

The JSON for this can be generated using the pScheduler command line interface and `jq`:
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

For a test to `192.0.2.86`, the specification shown above  would be changed to read as follows:
```
{
  "spec": {
    "dest": "192.0.2.86",
    "schema": 1
  },
  "type": "throughput"
}
```


### DNS

**TODO: Write this**


### The Callback

**TODO: Write this**

```
    ...
    "callback": {
        "_href": "https://localhost/pshooter/",
        "_params": {
            "pretty": "one",
            "foo": "bar"
        },
        "_headers": {
            "#X!Bad!Header": "bad",
            "X-Fake-Parameter": "gobsmacked",
            "X-Faker-Parameter": "gobsmackeder"
        },
        "retry-policy": [
            {"attempts": 2, "wait": "PT1S"},
            {"attempts": 2, "wait": "PT2S"},
            {"attempts": 2, "wait": "PT3S"}
        ]
    }
    ...
```


## Retreived Task Format

**TODO: Write this**
