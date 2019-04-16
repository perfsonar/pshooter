#
# Makefile for pShooter Programs
#
# The following variables must be provided externally:
#
#   COMMANDDIR - Location for installed programs
#   DAEMONDIR - Where daemon programs should be installed
#   DSNFILE - Location of DSN file for database logins
#   AUTHFILE - Location of pScheuler proxy auth file
#   UNITDIR - Location for installed systemd units
#   PGPASSFILE - Path to PostgreSQL password file
#   PGSERVICE - Name of the PostgreSQL systemd service
#   PGUSER - Name of pShooter PostgreSQL account
#   PSUSER - Name of pShooter user account
#   RUNDIR - Location of run directory (nominally /run)
#   VAR - Location of /var directory
#


BINS=pshooter
COMMANDS=debug internal
DAEMONS=service

UNITS=$(DAEMONS:%=service-%)

CONFIGS=$(DAEMONS:%=%.conf)

default: build



pshooter: pshooter.raw
ifndef COMMANDSINSTALLED
	@echo No COMMANDSINSTALLED specified for build
	@false
endif
	sed \
		-e 's|__COMMANDS__|$(COMMANDSINSTALLED)|g' \
		< $< > $@
	@if egrep -e '__[A-Z_]+__' $@ ; then \
		echo "Found un-substituted values in processed file $@" ; \
		false ; \
	fi
TO_CLEAN += pshooter


internal: internal.raw
ifndef INTERNALSDIR
	@echo No INTERNALSDIR specified for build
	@false
endif
	sed \
		-e 's|__INTERNALS__|$(INTERNALSDIR)|g' \
		< $< > $@
	@if egrep -e '__[A-Z_]+__' $@ ; then \
		echo "Found un-substituted values in processed file $@" ; \
		false ; \
	fi
TO_CLEAN += internal



debug: debug.raw
ifndef PSUSER
	@echo No PSUSER specified for build
	@false
endif
	sed \
		-e 's|__PSUSER__|$(PSUSER)|g' \
		-e 's|__RUNDIR__|$(RUNDIR)|g' \
		< $< > $@
	@if egrep -e '__[A-Z_]+__' $@ ; then \
		echo "Found un-substituted values in processed file $@" ; \
		false ; \
	fi
TO_CLEAN += debug



$(UNITS): service-template.raw
ifndef CONFIGDIR
	@echo No CONFIGDIR specified for build
	@false
endif
ifndef DAEMONDIR
	@echo No DAEMONDIR specified for build
	@false
endif
ifndef DSNFILE
	@echo No DSNFILE specified for build
	@false
endif
ifndef AUTHFILE
	@echo No AUTHFILE specified for build
	@false
endif
ifndef LOGDIR
	@echo No LOGDIR specified for build
	@false
endif
ifndef PSUSER
	@echo No PSUSER specified for build
	@false
endif
ifndef PGSERVICE
	@echo No PGSERVICE specified for build
	@false
endif
ifndef RUNDIR
	@echo No RUNDIR specified for build
	@false
endif
ifndef VAR
	@echo No VAR specified for build
	@false
endif
	sed \
		-e 's|__CONFIGDIR__|$(CONFIGDIR)|g' \
		-e 's|__DAEMONDIR__|$(DAEMONDIR)|g' \
		-e 's|__DSN__|$(DSNFILE)|g' \
		-e 's|__AUTH__|$(AUTHFILE)|g' \
		-e 's|__PROG__|$(@:service-%=%)|g' \
		-e 's|__PSUSER__|$(PSUSER)|g' \
		-e 's|__RUNDIR__|$(RUNDIR)|g' \
		-e 's|__VAR__|$(VAR)|g' \
		-e 's|__LOGDIR__|$(LOGDIR)|g' \
		-e 's|__PGSERVICE__|$(PGSERVICE)|g' \
		< $< > $@
	@if egrep -e '__[A-Z_]+__' $@ ; then \
		echo "Found un-substituted values in processed file $@" ; \
		false ; \
	fi
TO_CLEAN += $(UNITS)


$(CONFIGS): config-template.raw
	sed \
		-e 's|__PROG__|$(@:%.conf=%)|g' \
		< $< > $@
	@if egrep -e '__[A-Z_]+__' $@ ; then \
		echo "Found un-substituted values in processed file $@" ; \
		false ; \
	fi
TO_CLEAN += $(CONFIGS)


build: $(DAEMONS) $(INITS) $(UNITS) $(CONFIGS) $(COMMANDS) $(BINS)
	python -m compileall .



install: build
ifndef BINDIR
	@echo No BINDIR specified for installation
	@false
endif
ifndef CONFIGDIR
	@echo No CONFIGDIR specified for installation
	@false
endif
ifndef COMMANDDIR
	@echo No COMMANDDIR specified for installation
	@false
endif
ifndef DAEMONDIR
	@echo No DAEMONDIR specified for installation
	@false
endif
ifndef AUTHFILE
	@echo No AUTHFILE specified for installation
	@false
endif
	mkdir -p $(BINDIR)
	cp -f $(BINS) $(BINDIR)
	chmod 555 $(BINS:%=$(BINDIR)/%)
	mkdir -p $(CONFIGDIR)
	cp -f $(CONFIGS) $(CONFIGDIR)
	chmod 600 $(CONFIGS:%=$(CONFIGDIR)/%)
	mkdir -p $(COMMANDDIR)
	cp -f $(COMMANDS) $(COMMANDDIR)
	chmod 555 $(COMMANDS:%=$(COMMANDDIR)/%)
	mkdir -p $(DAEMONDIR)
	cp -f $(DAEMONS) $(DAEMONDIR)
	chmod 555 $(DAEMONS:%=$(DAEMONDIR)/%)
	cp -f *.pyc $(DAEMONDIR)
	chmod 555 $(DAEMONDIR)/*.pyc
	mkdir -p $(shell dirname $(AUTHFILE))
	cp auth $(AUTHFILE)
	chmod 400 $(AUTHFILE)
ifdef UNITDIR
	mkdir -p $(UNITDIR)
	@for SCRIPT in $(DAEMONS) ; \
	do \
		echo "Installing service for $${SCRIPT}" ; \
		cp -f service-$${SCRIPT} $(UNITDIR)/pshooter-$${SCRIPT}.service ; \
		chmod 444 $(UNITDIR)/pshooter-$${SCRIPT}.service ; \
	done
endif
TO_CLEAN += *.pyc


clean:
	rm -rf $(TO_CLEAN) *~
