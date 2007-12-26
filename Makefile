.SUFFIXES: .py .tmpl


DESTDIR = /opt/quicklook
OWNER = root
GROUP = root


CHEETAH = cheetah
CHEETAH_FLAGS = --nobackup


TEMPLATES = templates/processes/index.tmpl \
            templates/processes/load.tmpl \
            templates/processes/forks.tmpl \
            templates/disks/index.tmpl \
            templates/disks/detailed.tmpl \
            templates/cpu/index.tmpl \
            templates/memory/index.tmpl \
            templates/connections/index.tmpl \
            templates/counters/index.tmpl \
            templates/counters/detailed.tmpl \
            templates/ups/index.tmpl \
            templates/ups/detailed.tmpl \
            templates/skeleton.tmpl \
            templates/welcome/index.tmpl

PAGES := $(patsubst %.tmpl, %.py, $(TEMPLATES))


.tmpl.py:
	$(CHEETAH) compile $(CHEETAH_FLAGS) $<

all: $(PAGES)

install: $(PAGES)
	install -m 0755 -o $(OWNER) -g $(GROUP) -d $(DESTDIR)
	install -m 0755 -o $(OWNER) -g $(GROUP) stats.py $(DESTDIR)
	install -m 0755 -o $(OWNER) -g $(GROUP) -d $(DESTDIR)/templates
	find templates -name '*.py' | xargs -i install -m 0644 -o $(OWNER) -g $(GROUP) -D {} $(DESTDIR)/{}
	install -m 0755 -d $(DESTDIR)/components
	find components -name '*.py' | xargs -i install -m 0644 -o $(OWNER) -g $(GROUP) -D {} $(DESTDIR)/{}

clean:
	rm -f $(PAGES)
	find . -name '*.pyc' | xargs rm -f
	find . -name '*~' | xargs rm -f
