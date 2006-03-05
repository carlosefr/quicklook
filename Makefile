.SUFFIXES: .py .tmpl

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
            templates/skeleton.tmpl \
            templates/welcome/index.tmpl

PAGES := $(patsubst %.tmpl, %.py, $(TEMPLATES))


all: $(PAGES)

.tmpl.py:
	$(CHEETAH) compile $(CHEETAH_FLAGS) $<

clean:
	rm -f $(PAGES)
	find . -name '*.pyc' | xargs rm -f
	find . -name '*~' | xargs rm -f
