
# pShooter

pShooter is a tool for automating the process of 

An automated troubleshooter for use with pScheduler

A full description and a demonstration of a prototype version of
pShooter can be found [on
YouTube](https://www.youtube.com/watch?v=2HUY6b5T9DM).

## The API


`/api` - `GET` returns the API version supported by the server as an
integer.

`/hostname` - `GET` returns the host's name as a string.

`/stat/tasks/`_state_ - `GET` returns the number of tasks in the
`<state>` state as an integer, where _state_ is one of `pending`,
`prep`, `trace`, `running`, `callback`, `finished` or `failed`.



`/tasks` - `POST` creates a new task and returns its URL as a non-JSON
string (i.e., unquoted).  See _Posted Task Format_, below, for details
on the required input.  **TODO**: Make that a link.

`/tasks/`_UUID_ - `GET` returns the task in its current state as a
JSON object.  See _Retrived Task Format_, below, for details on the
contents of the object.  `DELETE` cancels the task if it is still
pending and the request was received from the local host or the same
one that originally `POST`ed it.


## Posted Task Format

pShooter is tasked with an HTTP `POST` to the `/pshooter/tasks` 


{
    "schema": 1,

    "path": ...,
    "test": { ... },
    "dns": { ... },
    "callback": { ... }
}

### The Path

The `path` pair specifies

If the path is a string, it will be interpreted as an IP address and 


### The Test


### DNS


### The Callback

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


### Reference


## Retreived Task Format

TODO: Write this.