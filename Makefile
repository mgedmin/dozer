PYTHON = python3

# Used by release.mk
FILE_WITH_VERSION = setup.py
FILE_WITH_CHANGELOG = CHANGELOG.rst
CHANGELOG_DATE_FORMAT = %B %e, %Y


.PHONY: all
all: bin/pytest bin/tox bin/coverage local-install  ##: set up a local virtualenv (default target)

.PHONY: test
test:                           ##: run tests
	tox -p auto

.PHONY: coverage
coverage: bin/pytest bin/coverage local-install  ##: measure test coverage
	bin/coverage run -m pytest
	bin/coverage report -m --fail-under=100

.PHONY: clean
clean:                          ##: remove build artifacts
	rm -rf .venv bin
	find -name '*.pyc' -delete


include release.mk


bin/pytest: | bin/pip
	bin/pip install pytest
	ln -srf .venv/$@ bin/

bin/tox: | bin/pip
	bin/pip install tox
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
	.venv/bin/pip install -U pip setuptools wheel

bin:
	mkdir $@
