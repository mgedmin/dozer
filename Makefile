# Which Python interpreter do you want to use
PYTHON = python

# Used by make release
FILE_WITH_VERSION = setup.py
FILE_WITH_CHANGELOG = CHANGELOG.rst
CHANGELOG_DATE_FORMAT = %B %e, %Y


.PHONY: all
all: bin/nosetests bin/detox bin/tox bin/coverage local-install

.PHONY: test
test: bin/nosetests local-install
	bin/nosetests --with-id

.PHONY: check
check: bin/detox local-install
	bin/detox

.PHONY: coverage
coverage: bin/nosetests bin/coverage local-install
	bin/nosetests --with-coverage --cover-erase --cover-inclusive --cover-package=dozer --with-id

.PHONY: clean
clean:
	rm -rf .venv bin
	find -name '*.pyc' -delete


include release.mk


bin/nosetests: | bin/pip
	bin/pip install nose
	ln -srf .venv/$@ bin/

bin/tox: | bin/pip
	bin/pip install tox
	ln -srf .venv/$@ bin/

bin/detox: | bin/pip
	bin/pip install detox
	ln -srf .venv/$@ bin/

bin/coverage: | bin/pip
	bin/pip install coverage
	ln -srf .venv/$@ bin/

local-install: .venv/lib/python*/site-packages/Dozer.egg-link
.venv/lib/python*/site-packages/Dozer.egg-link: setup.py
	bin/pip install -e '.[test]'

bin/pip: | .venv/bin/pip bin
	ln -srf .venv/bin/pip bin/

bin/python: | .venv/bin/python bin
	ln -srf .venv/$@ bin/

.venv/bin/python .venv/bin/pip:
	virtualenv -p $(PYTHON) .venv

bin:
	mkdir $@
