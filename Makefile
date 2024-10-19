SHELL   = /bin/bash
.ONESHELL:

PYTHON  = python
PIP     = ./venv/bin/pip
PACKAGE = pg_schema_version

#
# cleanup
#

.PHONY: clean
clean:
	$(RM) *~
	$(RM) -r __pycache__ $(PACKAGE)/__pycache__ .ruff_cache dist
	$(MAKE) -C tests $@

.PHONY: clean.venv
clean.venv: clean
	$(RM) -r venv $(PACKAGE).egg-info

.PHONY: clean.dev
clean.dev: clean clean.venv

#
# environment
#

.PHONY: dev
dev: venv.dev

venv:
	$(PYTHON) -m venv venv
	$(PIP) install -e .

.PHONY: venv.dev
venv.dev: venv/.dev

venv/.dev: venv
	source venv/bin/activate
	$(PIP) install -e .[dev]
	touch $@

.PHONY: venv.pub
venv.pub: venv/.pub

venv/.pub: venv
	source venv/bin/activate
	$(PIP) install -e .[pub]
	touch $@

#
# checks
#

.PHONY: check.ruff
check.ruff: venv.dev
	source venv/bin/activate
	ruff check $(PACKAGE)

.PHONY: check.pyright
check.pyright: venv.dev
	source venv/bin/activate
	pyright $(PACKAGE)

.PHONY: check.md
check.md: venv.dev
	source venv/bin/activate
	pymarkdownlnt scan *.md

.PHONY: check.test
check.test: venv
	source venv/bin/activate
	$(MAKE) -C tests $@

.PHONY: check.coverage
check.coverage: venv.dev
	source venv/bin/activate
	$(MAKE) -C tests $@

.NOTPARALLEL: check.test check.coverage

.PHONY: check
check: check.ruff check.pyright check.test check.coverage check.md

#
# publication
#

# distribution
dist: venv.pub
	source venv/bin/activate
	$(PYTHON) -m build

.PHONY: publish
publish: dist
	# provide pypi ids in ~/.pypirc
	echo ./venv/bin/twine upload dist/*
