
# pShooter

pShooter is a tool that automates part of the process of troubleshooting network problems along a path between two hosts

running pScheduler tests to as many perfSONAR nodes as can be found along a path between two hosts.  It consists of a web service with a [REST API](#the-api) and a scheme for placing information into the Domain Name Service that can be used to locate perfSONAR nodes in close proximity to the path.


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

**TODO: Write this**


### The Test

**TODO: Write this**


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
