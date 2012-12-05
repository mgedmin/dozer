# Which Python interpreter do you want to use
PYTHON = python

# Directory that will be nuked and created by 'make distcheck'
TMPDIR = tmp

# Used by make release
FILE_WITH_VERSION = setup.py
FILE_WITH_CHANGELOG = CHANGELOG.rst


all:
	# There's nothing that needs building in Dozer.

test:
	# No tests yet :(

dist:
	$(PYTHON) setup.py sdist

distcheck:
	@test -z "`hg status 2>&1`" || \
	  { echo; echo "Your working tree is not clean" 1>&2; hg status; exit 1; }
	$(MAKE) dist
	pkg_and_version=`$(PYTHON) setup.py --name`-`$(PYTHON) setup.py --version` && \
	  rm -rf $(TMPDIR) && \
	  mkdir $(TMPDIR) && \
	  hg archive $(TMPDIR)/tree/ && \
	  cd $(TMPDIR) && \
	  tar xvzf ../dist/$$pkg_and_version.tar.gz && \
	  diff -ur $$pkg_and_version tree -x PKG-INFO -x setup.cfg -x '*.egg-info' -x '.hg*' && \
	  cd $$pkg_and_version && \
	  $(MAKE) dist test && \
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
	@echo "  $(PYTHON) setup.py sdist register upload && hg tag v`$(PYTHON) setup.py --version`"
	@echo
	@echo "Please increment the version number in $(FILE_WITH_VERSION)"
	@echo "and add a new empty entry at the top of the changelog in $(FILE_WITH_CHANGELOG), then"
	@echo
	@echo '  hg commit -m "Post-release version bump" && hg push'
	@echo


.PHONY: all test dist distcheck releasechecklist release
