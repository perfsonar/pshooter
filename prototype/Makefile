#
# Makefile for Internet2 Static Zone Data and Test Templates
#

# Configurables

TRACE=prp
TEST=throughput

# End Configurables


default: test


#
# Static Resolver Data
#

STATIC_ZONE=static-resolver/static-resolver.conf
$(STATIC_ZONE):
	@echo
	@echo "Building static resolver configuration"
	@echo
	$(MAKE) -C static-resolver

zonedata: $(STATIC_ZONE)


#
# Test
#

TEST_FILE=test.json
TEST_TEMPLATE=tests/$(TEST)

TRACE_FILE=traces/$(TRACE)

$(TEST_FILE): $(TRACE_FILE) $(TEST_TEMPLATE)
	@echo
	@echo "Preparing the pShooter test template for testing $(TEST) to $(TRACE)"
	@echo
	jq -s '{ "path": [ .[0].paths[0] | .[] | .ip // empty ], "test": .[1] }' \
	$(TRACE_FILE) $(TEST_TEMPLATE) \
	| jq '.path = [ "127.0.0.1" ] + .path' \
	| jq 'del(.test["#"])' \
	> $@
TO_CLEAN += $(TEST_FILE)

test: $(TEST_FILE)


#
# Run
#

RUN_RESULT=result.json
$(RUN_RESULT): $(TEST_FILE) $(STATIC_ZONE)
	@echo
	@echo Running the test
	@echo
	./bin/run-test $(TEST_FILE) $(STATIC_ZONE) > $@
TO_CLEAN += $(RUN_RESULT)


TEXT_RESULT=output
$(TEXT_RESULT): $(RUN_RESULT)
	@echo
	@echo Producing human-readable output
	@echo
	./bin/dump-result < $< > $@
TO_CLEAN += $(TEXT_RESULT)


demo: clean $(TEXT_RESULT)
	less $(TEXT_RESULT)




#
# Etc...
#

clean:
	$(MAKE) -C static-resolver $@
	$(MAKE) -C bin $@
	rm -rf $(TO_CLEAN)
	-( set pipefail && find . -name "*~" | grep '' | xargs rm -rf )


TARBALL=nrp-demo.tar
$(TARBALL): clean
	rm -f $@
	tar cf $@ $(wildcard *)
TO_CLEAN += $(TARBALL)

tar: $(TARBALL)
