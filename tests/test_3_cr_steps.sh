#! /bin/bash

source psv-test-infra.sh

# create step by step
check_nop "3.0"
check_run "3.1" 0 app "create"
check_run "3.2" 0 app "create:dry"
check_run "3.3" 0 bla "create:dry"
check_nop "3.4"
check_run "3.5" 0 app "create:wet"
check_run "3.6" 0 bla "create:wet"
check_cnt "3.7" 3
check_ver "3.8" app 0
check_run "3.9" 0 bla "create:wet" bla_1.sql
check_ver "3.a" bla 1
check_run "3.b" 0 bla "create:wet" bla_1.sql bla_2.sql
check_ver "3.c" bla 2
check_run "3.d" 0 bla "create:wet" bla_1.sql bla_2.sql bla_3.sql
check_ver "3.e" bla 3
check_run "3.f" 0 bla "create:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "3.g" bla 4
check_run "3.h" 0 bla "remove:wet"
check_nop "3.i"

echo "passed: $OK/$TEST"
exit $KO
