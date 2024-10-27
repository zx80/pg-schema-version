#! /bin/bash

source psv-test-infra.sh

# with foo table
check_nop "6.0"
check_run "6.1" 0 foo "create" foo_1.sql
check_run "6.2" 0 foo "create:dry" foo_1.sql
check_nop "6.3"
check_run "6.4" 0 foo "create:wet" foo_1.sql
check_cnt "6.5" 2
check_ver "6.6" foo 1
check_que "6.7" 0 "SELECT COUNT(*) FROM Foo"
check_run "6.8" 0 foo "create:dry" foo_1.sql foo_2.sql  # NOP
check_ver "6.6" foo 1
check_que "6.7" 0 "SELECT COUNT(*) FROM Foo"
check_run "6.8" 0 foo "create:wet" foo_1.sql foo_2.sql
check_ver "6.9" foo 2
check_que "6.a" 2 "SELECT COUNT(*) FROM Foo"
check_run "6.b" 0 foo "create:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "6.c" foo 3
check_que "6.d" 4 "SELECT COUNT(*) FROM Foo"
check_run "6.h" 0 app "remove:wet"
check_nop "6.i"
$pg -c "DROP TABLE Foo" $db  # cleanup

echo "passed: $OK/$TEST"
exit $KO
