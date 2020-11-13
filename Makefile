PYTHON = python3

# Used by release.mk
FILE_WITH_VERSION = setup.py
FILE_WITH_CHANGELOG = CHANGELOG.rst
CHANGELOG_DATE_FORMAT = %B %e, %Y


.PHONY: all
all:                            ##: pre-build tox environments
	tox -p auto --notest

.PHONY: test
test:                           ##: run tests
	tox -p auto

.PHONY: coverage
coverage:                       ##: measure test coverage
	tox -e coverage

.PHONY: clean
clean:                          ##: remove build artifacts
	rm -rf .venv bin .tox
	find -name '*.pyc' -delete


include release.mk
