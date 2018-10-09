#
# Makefile for Internet2 Static Zone Data and Test Templates
#

default: build


RAWS=$(wildcard *.raw)
CONVERTED_RAWS=$(RAWS:%.raw=%.static)
STATICS=$(CONVERTED_RAWS) $(wildcard *.static)



%.static: %.raw
	./raw-to-static < $< > $@
TO_CLEAN += $(CONVERTED_RAWS)

STATIC_DATA = static-resolver.conf
$(STATIC_DATA): $(STATICS)
	jq -s 'reduce .[] as $$item ({}; . * $$item)' $(STATICS) > $@
TO_CLEAN += $(STATIC_DATA)


build: $(STATIC_DATA)

clean:
	rm -rf $(TO_CLEAN) *~
