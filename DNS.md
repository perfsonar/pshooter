# DNS as a Locator Service for Nearby perfSONAR Nodes

## Introduction

Determination of perfSONAR nodes to use when troubleshooting a
performance problem has historically been a manual process aided by
the perfSONAR Lookup Service (LS) maintained by ESNet.  While the LS
provides useful information, its major drawback is having a model of
location based on geography rather than network topology.  Once a node
physically near points of interest is identified, additional work is
required to determine whether or not it can provide suitable
measurements.  Occasionally, that work involves test driving a node to
see whether or not it is suitable.  There have been attempts to
determine the nearest node automatically by analyzing large numbers of
traceroute results that have brought mixed results.

A common method of troubleshooting performance problems involves
performing measurements between an ever-smaller subset of the path
having difficulties until the problem is no longer observed.  Often,
points along these paths are well-known routers on campus, connector,
regional and national networks.  The measurement infrastructure on
those networks is put there by their operators, who are in the best
position to know what perfSONAR nodes will provide good results
without disrupting their own operations.

This document describes a scheme to let network operators share that
knowledge in an automated, flexible way.  The question it aims to
answer is "the path between point _A_ and point _B_ passes through
point _C_; what nearby perfSONAR node should be used to make
measurements where _C_ is one of the endpoints?" The answer will be
one of the following:

 * Use perfSONAR node _N_ to make the measurement.
 * Direct your request to universal resource locator _U_ to receive an answer.
 * There is no known recommendation for making measurements to _C_.


## The DNS Foundation

The selected means for delivering this information is the Domain Name
Service (DNS) used across the Internet to fully-qualified domain names
(FQDNs) into IP addresses and other information.  It was selected over
other approaches for a number of reasons:

 * **Ubiquity.** Few, if any, operators of networks are not also
     running a DNS service.

 * **Stability.** The root parts of the infrastructure are
     well-maintained, as is the software most often used to provide
     the service.

 * **Resilience.** The ability to cache records makes it more likely
     that often-used records will be available nearby in the event the
     authoritative sources are not.

 * **Availability.** Access to DNS is rarely blocked by firewalls.
     When it is, full, indirect access is usually provided by proxy.

 * **Flexibility.** Views, a feature of BIND and other DNS servers,
     can be used to provide different answers to different
     questioners.


## DNS Records

To make a nearby perfSONAR node locatable, two types of records must
be configured in DNS.


### Pointer Records

To make a perfSONAR node locatable for an interface on a device, the
interface's IP address(es) must be resolvable to a FQDN via a `PTR`
record in the `in-addr.arpa` zone for IPv4 or `ip6.arpa` for IPv6.
For example:

| Record in `.arpa` Zone                  | PTR Record            |
|:--------------------------------------- |:--------------------- |
| `99.100.151.198.in-addr.apra`           | `gw6.example.net.`    |
| `99.0. ... .0.8.b.d.0.1.0.0.2.ip6.arpa` | `gw6-v6.example.net.` |


### Locator Records

Location information is provided by a specially-formatted `TXT` record
(described in [_Record Format_](#Record-Format), below).  Each `TXT`
record is assigned to a FQDN derived from that named by the `PTR`
record for the interface's IP address.  The derived name is used
rather than the name in the `PTR` record to avoid collisions with
other `TXT` records a site may be using.  (While DNS does support
multiple `TXT` records per zone entry, its use is uncommon and may be
confusing to applications not coded to be aware of this.)

The locator record name is formed by adding a prefix to the
lowest-level label in the FQDN.  There are two types of prefixes,
address-family-specific and non-address family-specific.  The prefixes
are as follows:

| Category | Prefix |
|:------------------------------------------ |:--------------------- |
| Address Family-Specific for IPv4 Addresses | `_ipv4._perfsonar.` |
| Address Family-Specific for IPv6 Addresses | `_ipv6._perfsonar.` |
| Non-Address Family-Specific                | `_perfsonar.`        |

For example, the FQDNs described above would have locator records
named as follows:

| FQDN | Locator Record |
|:-------------------- |:-------------------------------------- |
| `gw6.example.net`    | `_ipv4._perfsonar.gw6.example.net.`    |
| `gw6-v6.example.net` | `_ipv6._perfsonar.gw6-v6.example.net.` |

Additionally, a non-specific FQDN of `_perfsonar.gw6.example.net.` may
be made available to cover either case without having to create
individual records for IPv4 and IPv6.  This record will be queried as
a last resort when an address family-specific record is not available.


## Higher-Level Domain Searching

To simplify deployment of this scheme, implementations of software
using it should be able to search for locator records in higher-level
domains.  This would allow for an entire subdomain served by a single
perfSONAR instance to be specified with a single record or as a
mechanism for falling back to a default for a top-level domain.  After
a failure to find a locator record for the FQDN, the first label is
removed and the search is carried out again.  The process repeats
until a locator record is found or no labels remain.

For example, the complete search sequence for the IPv4 host
`gw6.nyc.example.net` would be as follows:

| Step | Partial FQDN          | Locator Record FQDN |
|:----:|:--------------------- |:--------------------------------------- |
| 1    | `gw6.nyc.example.net` | `_ipv4._perfsonar.gw6.nyc.example.net.` |
| 2    | `gw6.nyc.example.net` | `_perfsonar.gw6.nyc.example.net.`       |
| 3    | `nyc.example.net`     | `_ipv4._perfsonar.nyc.example.net.`     |
| 4    | `nyc.example.net`     | `_perfsonar.nyc.example.net.`           |
| 5    | `example.net`         | `_ipv4._perfsonar.example.net.`         |
| 6    | `example.net`         | `_perfsonar.example.net.`               |
| 7    | `net`                 | `_ipv4._perfsonar.net.`                 |
| 8    | `net`                 | `_perfsonar.net.`                       |


## Record Format

The content of the locator record returned by DNS is a valid JSON.  To
accommodate common limitations of many DNS servers and client
libraries, the locator record will not exceed 255 bytes in length.

The content of the record is a single [JavaScript Object
Notation](https://www.json.org) (JSON, defined by ECMA 404) object
containing these pairs:

| Pair | Description | Example(s) |
|:---- |:----------- |:---------- |
| `schema` | A positive integer indicating the schema version number for the data.  This pair is optional and will have a default value of `1` if not provided.| `2` |
| `href`   | A string containing a URL where a complete record may be found, useful for redirecting to sources of longer records.  If present, all other pairs in the record will be ignored.  See [_URL Requests_](#URL_Requests), below, for additional information on the semantics of retrieving these records. | `https://findmyps.example.net/rtr3-e0_0_1` |
| `pscheduler` | A string indicating the hostname and, optionally, port of a pScheduler server on the perfSONAR node to contact for arranging a measurement. | `ps6.example.net:3713` |

A complete example of a locator record is as follows (newlines added
for readability):

```
{
  "schema": 1,
  "pscheduler": "ps.nyc.example.net:4349"
}
```


## URL Requests

Locator records containing a `href` pair redirect the client to find
the locator record at the specified URL.  An `href` pair may appear in
locator records retrieved from DNS or from a location specified in an
`href` pair.  In the interest of avoiding infinite loops, clients
should be expected to treat having seen five redirections as a
no-information-found condition.

For `http` and `https` , the likely-usual schemes:

 * Returned documents will have a `Content-Type` of `application/json`
   and a status code of `200`.

 * If there is no document available (i.e., there is no information
   for the requested host), the status code will be `404`.

 * Clients must correctly handle HTTP redirect status codes `301` ,
   `302` , `303` , `307` and `308`.

For other schemes (e.g., `ftp`), clients should emulate the `http`
behaviors as closely as possible in an scheme-appropriate way.


## Location Algorithm

The steps for identifying a perfSONAR node to be used as a test point
for an address are as follows:

1. Determine the DNS record type for the address.
 * `198.151.100.86`  &rarr;  IPv4  &rarr;  `A`

2. Reverse-resolve the address to a FQDN using a `PTR` record.
 * `86.100.151.198.in-addr.arpa`  &rarr;  `core2.example.net.`

3. Prepend the appropriate suffix to the lowest-level domain label.
 * `core2.example.net.`  &rarr;  `_ipv4._perfsonar.core2.example.net.`

4. Resolve the new name to a `TXT` record:
 * `_ipv4._perfsonar.core2.example.net.`  &rarr;  _Record Text_

5. If no such record exists, remove the address family specifier and try
again:
 * `_perfsonar.example.net.`  &rarr;  _Record Text_

6. If no such record exists and there is more than one label remaining
in the FQDN, strip the lowest-level label (e.g., `core2.example.net`
becomes `example.net` ) and go back to step 3.

7. If no record was found, there is no perfSONAR node known to be
close to the original device.  Stop here.

8. If the record text contains a `href` pair, fetch the document at
the location its value specifies and use it in the following steps,
repeating this step up to five times if a fetched document contains a
`href` pair.
 * `{ "schema": 1, "pscheduler": "ps6.example.net" }`

9. Use the value of the `pscheduler` pair in the JSON to construct a
URL for the pScheduler API on the host:
 * `https://ps6.example.net/pscheduler`
