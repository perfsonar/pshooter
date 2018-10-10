# Instructions for Running the pShooter Demo

## Prerequisites:

 * Linux system with access to the Internet
 * Vagrant
 * VirtualBox


## Preparation

 1 Clone this Git repository
 1 `cd pshooter/prototype`
 1 `vagrant up`
 1 `vagrant ssh`


## Prototype Directories

The `prototype` directory contains a Makefile and the following
subdirectories:

 * `traces` - Contains the results of trace tests from I2/Merit to
hosts where the path traverses I2.  Choices are prp (the default),
ucla and washington.

 * `tests` - Contains canned test templates.  Choices are rtt,
simplestream and throughput (the default).  The throughput test is
short-duration and bandwidth-capped, so don't expect meaningful
results out of it.  The simplestream test is a good one to use if you
want something to quickly verify that everything is working properly.

 * `static-resolver` - Contains data about the Internet2 network and
others that maps IP addresses to perfSONAR nodes.  Data for the other
domains has been set up manually based on where some of the traces
went to provide access to off-network perfSONAR.

 * `bin` - Contains the prototype pShooter software.  Nothing to see
here.


## Running a Demo

The demo is run using `make`, and the simplest target is `demo`:

```
make demo
```

The program will produce some debug while it's running, then the
results will be piped through 'less' for reading.

The human-readable results will end up in a plain text file called
`output,` machine-readable (JSON) results will be in `result.json` and
the template fed to pShooter will be in `test.json`.

If you want to do a different test or use a differnt path, specify the
`TRACE` or `TEST` variable on the command line when you run `make`:

```
    make TRACE=prp TEST=rtt demo
```
