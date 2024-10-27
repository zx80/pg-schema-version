#! /bin/bash

source psv-test-infra.sh

# apply
check_nop "5.0"
check_run "5.1" 0 bla "apply" bla_1.sql bla_2.sql
check_run "5.2" 0 bla "apply:dry" bla_1.sql bla_2.sql
check_nop "5.3"
check_run "5.4" 0 bla "apply:wet" bla_1.sql bla_2.sql  # KO, need init and register
check_nop "5.5"
check_run "5.6" 0 bla "init:wet" bla_1.sql bla_2.sql
check_cnt "5.7" 1
check_run "5.8" 0 bla "apply:wet" bla_1.sql bla_2.sql  # KO, need register
check_cnt "5.9" 1
check_run "5.a" 0 bla "register:wet" bla_1.sql bla_2.sql
check_cnt "5.b" 2
check_ver "5.c" bla 0
check_run "5.d" 0 bla "apply:wet" bla_1.sql bla_2.sql
check_ver "5.e" bla 2
check_run "5.f" 0 bla "apply:wet" bla_3.sql bla_2.sql bla_1.sql  # out of order is ok
check_ver "5.g" bla 3
check_run "5.h" 0 bla "remove:wet"
check_nop "5.i"

echo "passed: $OK/$TEST"
exit $KO
