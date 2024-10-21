SHELL   = /bin/bash
.ONESHELL:

.PHONY: clean
clean:
	$(RM) .coverage bla.sql foo.sql acme.sql bad.sql tmp_*.sql

.PHONY: check.commands
check.commands:
	type psql || exit 1
	type pg-schema-version || exit 2

.NOTPARALLEL: check.test check.coverage

.PHONY: check.test
check.test: check.commands
	./test.sh || exit 3

.PHONY: check.coverage
check.coverage: clean check.commands
	export TEST_PSV="coverage run -a ../venv/bin/pg-schema-version"
	$(MAKE) check.test
	coverage report --show-missing --precision=1 --fail-under=100.0

# generate scripts
%.sql:
	pg-schema-version -a $* $*_*.sql > $@
