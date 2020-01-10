# pShooter Beta

This directory contains pre-built versions of the pShooter RPMs to be
used during the beta period.  It will be removed when pShooter is
released.


## Installation

**While pShooter will coexist peacefully with the rest of a perfSONAR
  node and can be removed without leaving a trace, installation of
  beta code on a production system is not recommended.**

 Build a perfSONAR node by
[installing](https://docs.perfsonar.net/install_centos.html) the
`perfsonar-testpoint` bundle.

Install all of the RPMs in this directory:
 * `yum -y install pshooter-*.rpm`

Verify that pShooter is functioning:
 * `curl -sk --location https://localhost/pshooter`
 * `"This is the pShooter API server on localhost (HOST-NAME)."`


## Removal

pShooter can be removed from an existing host using this command

```
# yum -y erase 'pshooter-*'
```
