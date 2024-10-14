.PHONY: check.test
check.test:
	type psql || exit 1
	type pg-schema-version || exit 2
	./test.sh || exit 3
