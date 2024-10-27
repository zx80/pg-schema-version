#! /bin/bash

source psv-test-infra.sh

# catchup
check_nop "7.0"
check_que "7.1" 0 "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE tablename = 'Foo'"
check_run "7.2" 0 foo "catchup" foo_1.sql
check_run "7.3" 0 foo "catchup:dry" foo_1.sql
check_nop "7.4"
check_run "7.5" 0 foo "catchup:wet" foo_1.sql
check_cnt "7.6" 2
check_ver "7.7" foo 1
check_run "7.8" 0 foo "catchup:wet" foo_1.sql foo_2.sql
check_ver "7.9" foo 2
check_run "7.a" 0 foo "catchup:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "7.b" foo 3
check_run "7.c" 0 foo "catchup:2:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "7.d" foo 2
check_run "7.e" 0 foo "catchup:1:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "7.f" foo 1
check_run "7.g" 0 foo "catchup:2:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "7.h" foo 2
check_run "7.i" 0 foo "catchup:3:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "7.j" foo 3
check_que "7.k" 0 "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE tablename = 'Foo'"
check_run "7.l" 0 app "remove:wet"
check_nop "7.m"

echo "passed: $OK/$TEST"
exit $KO
