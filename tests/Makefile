SHELL   = /bin/bash
.ONESHELL:

TEST_DB = pg_schema_version_test_database
export TEST_DB

.PHONY: clean
clean:
	$(RM) .coverage bla.sql foo.sql acme.sql bad.sql tmp_*.sql .test_db
	dropdb $(TEST_PG_OPTS) $(TEST_DB) || true

.PHONY: check.commands
check.commands:
	type psql || exit 1
	type pg-schema-version || exit 2

TEST.sh = $(wildcard test_*.sh)
TEST.ex = $(TEST.sh:%.sh=%.ex)

.NOTPARALLEL: check.test check.coverage
.NOTPARALLEL: $(TEST.ex)

.test_db:
	createdb $(TEST_PG_OPTS) $(TEST_DB)
	touch $@

$(TEST.ex): .test_db

test_%.ex: test_%.sh
	echo "# running $<"
	./$<

.PHONY: check.test
check.test: check.commands
	$(MAKE) $(TEST.ex)

.PHONY: check.coverage
check.coverage: clean check.commands
	export TEST_PSV="coverage run -a ../venv/bin/pg-schema-version"
	$(MAKE) check.test
	coverage report --show-missing --precision=1 --fail-under=100.0

# generate scripts
%.sql:
	pg-schema-version -a $* $*_*.sql > $@
