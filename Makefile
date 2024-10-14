SHELL   = /bin/bash
.ONESHELL:

PYTHON  = python
PACKAGE = pg_schema_version

#
# cleanup
#

.PHONY: clean
clean:
	$(RM) *~
	$(RM) -r __pycache__ $(PACKAGE)/__pycache__ .ruff_cache dist

.PHONY: clean.venv
clean.venv: clean
	$(RM) -r venv $(PACKAGE).egg-info

.PHONY: clean.dev
clean.dev: clean clean.venv

#
# environment
#

venv:
	$(PYTHON) -m venv venv
	./venv/bin/pip install -e .[dev,pub]

#
# checks
#

.PHONY: check.ruff
check.ruff: venv
	source venv/bin/activate
	ruff check $(PACKAGE)

.PHONY: check.pyright
check.pyright: venv
	source venv/bin/activate
	pyright $(PACKAGE)

.PHONY: check.test
check.test: venv
	source venv/bin/activate
	$(MAKE) -C tests $@

.PHONY: check
check: check.ruff check.pyright check.test

#
# publication
#

# distribution
dist: venv
	source venv/bin/activate
	$(PYTHON) -m build

.PHONY: publish
publish: dist
	# provide pypi ids in ~/.pypirc
	echo ./venv/bin/twine upload dist/*
