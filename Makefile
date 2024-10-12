SHELL   = /bin/bash
.ONESHELL:

PYTHON  = python
PACKAGE = pg_schema_version

.PHONY: clean
clean:
	$(RM) *~
	$(RM) -r __pycache__ $(PACKAGE)/__pycache__

.PHONY: clean.dev
clean.dev: clean
	$(RM) -r venv $(PACKAGE).egg-info

venv:
	$(PYTHON) -m venv venv
	./venv/bin/pip install -e .[dev]
