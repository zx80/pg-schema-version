#! /bin/bash

source psv-test-infra.sh

# apply with target version
check_nop "9.0"
check_run "9.1" 0 bla "create:1" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_run "9.2" 0 bla "create:1:dry" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_nop "9.3"
# simple register
check_run "9.4" 0 bla "create:0:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_cnt "9.5" 2
check_ver "9.6" psv 0
check_ver "9.7" bla 0
check_run "9.8" 0 bla "apply:1:dry" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "9.9" bla 0
# one step at a time, check version and descriptions
check_run "9.a" 0 bla "apply:0:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "9.b" bla 0
check_run "9.c" 0 bla "apply:1:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "9.d" bla 1
check_des "9.e" bla 1 "application bla initial schema"
check_run "9.f" 0 bla "apply:2:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "9.g" bla 2
check_des "9.h" bla 2 "application bla first upgrade"
check_run "9.i" 0 bla "apply:3:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "9.j" bla 3
check_des "9.k" bla 3 "application bla second upgrade"
check_run "9.l" 0 bla "apply:4:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "9.m" bla 4
# all descriptions are there
check_des "9.n" bla 1 "application bla initial schema"
check_des "9.o" bla 2 "application bla first upgrade"
check_des "9.p" bla 3 "application bla second upgrade"
check_des "9.q" bla 4 "application bla third upgrade"
check_run "9.r" 0 bla "status" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_run "9.s" 0 bla "remove:wet"
check_nop "9.t"

echo "passed: $OK/$TEST"
exit $KO
