.PHONY: clean
clean:
	$(RM) .coverage

.PHONY: check.commands
check.commands:
	type psql || exit 1
	type pg-schema-version || exit 2

.PHONY: check.test
check.test: check.commands
	./test.sh || exit 3

.PHONY: check.coverage
check.coverage: check.commands
	./test.sh "coverage run -a ../venv/bin/pg-schema-version"
	coverage report --show-missing --precision=1 --fail-under=100.0
