#! /bin/bash

source psv-test-infra.sh

# create including error detection
check_nop "4.0"
check_run "4.1" 0 app "create"
check_run "4.2" 0 app "create:dry"
check_nop "4.3"
check_run "4.4" 0 app "create:wet"
check_run "4.5" 0 bla "create:wet"
check_cnt "4.6" 3
check_ver "4.7" psv 0
check_ver "4.8" app 0
check_ver "4.9" bla 0
check_run "4.a" 0 bla "create:wet" bla_1.sql  # ok
check_ver "4.b" bla 1
check_run "4.c" 0 bla "create:wet" -p bla_3.sql bla_1.sql  # KO
check_run "4.d" 0 bla "create:wet" -p bla_3.sql bla_4.sql  # KO
check_run "4.e" 0 bla "create:wet" -p bla_4.sql bla_3.sql  # KO
check_ver "4.f" bla 1
check_run "4.g" 0 bla "create:wet" bla_1.sql bla_2.sql  # ok
check_ver "4.h" bla 2
check_run "4.i" 0 bla "create:wet" -p bla_1.sql bla_4.sql bla_2.sql  # KO
check_run "4.j" 0 bla "create:wet" -p bla_1.sql bla_2.sql bla_4.sql  # KO
check_run "4.k" 0 bla "create:wet" -p bla_1.sql bla_1.sql bla_2.sql  # KO
check_run "4.l" 0 bla "create:wet" -p bla_1.sql bla_4.sql bla_2.sql  # KO
check_ver "4.m" bla 2
check_run "4.n" 0 bla "create:wet" bla_1.sql bla_2.sql bla_3.sql  # ok
check_ver "4.o" bla 3
check_run "4.p" 0 bla "create:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql  # ok
check_ver "4.q" bla 4
check_run "4.r" 0 bla "remove:wet"
check_nop "4.s"

echo "passed: $OK/$TEST"
exit $KO
