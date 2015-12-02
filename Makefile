# Which Python interpreter do you want to use
PYTHON = python

# Directory that will be nuked and created by 'make distcheck'
TMPDIR = tmp

# Used by make release
FILE_WITH_VERSION = setup.py
FILE_WITH_CHANGELOG = CHANGELOG.rst

VCS_STATUS = git status --porcelain
VCS_EXPORT = git archive --format=tar --prefix=$(TMPDIR)/tree/ HEAD | tar -xf -
VCS_TAG = git tag
VCS_COMMIT_AND_PUSH = git commit -av -m "Post-release version bump" && git push && git push --tags


all: bin/nosetests bin/detox bin/tox bin/coverage local-install

test: bin/nosetests local-install
	bin/nosetests --with-id

check: bin/detox local-install
	bin/detox

coverage: bin/nosetests bin/coverage local-install
	bin/nosetests --with-coverage --cover-erase --cover-inclusive --cover-package=dozer --with-id

clean:
	rm -rf .venv bin
	find -name '*.pyc' -delete

dist:
	$(PYTHON) setup.py -q sdist

distcheck:
	@test -z "`$(VCS_STATUS) 2>&1`" || { echo; echo "Your working tree is not clean" 1>&2; $(VCS_STATUS); exit 1; }
	$(MAKE) dist
	pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	  rm -rf $(TMPDIR) && \
	  mkdir $(TMPDIR) && \
	  $(VCS_EXPORT) && \
	  cd $(TMPDIR) && \
	  tar xvzf ../dist/$$pkg_and_version.tar.gz && \
	  diff -ur $$pkg_and_version tree -x PKG-INFO -x setup.cfg -x '*.egg-info' && \
	  cd $$pkg_and_version && \
	  $(MAKE) dist check && \
	  cd .. && \
	  mkdir one two && \
	  cd one && \
	  tar xvzf ../../dist/$$pkg_and_version.tar.gz && \
	  cd ../two/ && \
	  tar xvzf ../$$pkg_and_version/dist/$$pkg_and_version.tar.gz && \
	  cd .. && \
	  diff -ur one two -x SOURCES.txt && \
	  cd .. && \
	  rm -rf $(TMPDIR) && \
	  echo "sdist seems to be ok"

releasechecklist:
	@$(PYTHON) setup.py --version | grep -qv dev || { \
	    echo "Please remove the 'dev' suffix from the version number in $(FILE_WITH_VERSION)"; exit 1; }
	@$(PYTHON) setup.py --long-description | rst2html --exit-status=2 > /dev/null
	@ver_and_date="`$(PYTHON) setup.py --version` (`echo \`env LC_ALL=C date +'%B %e, %Y'\``)" && \
	    grep -q "^$$ver_and_date$$" $(FILE_WITH_CHANGELOG) || { \
	        echo "$(FILE_WITH_CHANGELOG) has no entry for $$ver_and_date"; exit 1; }
	make distcheck

release: releasechecklist
	# I'm chicken so I won't actually do these things yet
	@echo "Please run"
	@echo
	@echo "  rm -rf dist && $(PYTHON) setup.py -q sdist bdist_wheel && twine upload dist/* && $(VCS_TAG) `$(PYTHON) setup.py --version`"
	@echo
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  $(VCS_COMMIT_AND_PUSH)'
	@echo


.PHONY: all test check dist distcheck releasechecklist release

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
