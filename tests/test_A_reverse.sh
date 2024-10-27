#! /bin/bash

source psv-test-infra.sh

all_bla=$(echo bla_*.sql)

# apply/reverse
check_nop "A.0"
check_run "A.1" 0 bla "create:wet" $all_bla
check_cnt "A.2" 2
check_ver "A.3" psv 0
check_ver "A.4" bla 4
check_run "A.5" 0 bla "reverse:4" $all_bla
check_run "A.6" 0 bla "reverse:4:dry" $all_bla
check_run "A.7" 0 bla "reverse:4:wet" $all_bla
check_ver "A.8" bla 4
check_run "A.9" 0 bla "reverse:3:wet" $all_bla
check_ver "A.a" bla 3
check_run "A.b" 0 bla "reverse:2:wet" $all_bla
check_ver "A.c" bla 2
check_run "A.d" 0 bla "reverse:1:wet" $all_bla
check_ver "A.e" bla 1
check_run "A.f" 0 bla "reverse:0:wet" $all_bla
check_ver "A.g" bla 0
check_run "A.h" 0 bla "apply:3:wet" $all_bla
check_ver "A.i" bla 3
check_run "A.j" 0 bla "reverse:1:wet" $all_bla
check_ver "A.k" bla 1
check_run "A.l" 0 bla "apply:4:wet" $all_bla
check_ver "A.m" bla 4
check_run "A.n" 0 bla "reverse:2:wet" $all_bla
check_ver "A.o" bla 2
check_run "A.p" 0 bla "reverse:0:wet" $all_bla
check_ver "A.q" bla 0
check_run "A.r" 0 bla "unregister:wet" $all_bla
check_cnt "A.s" 1
check_run "A.t" 0 bla "remove:wet" $all_bla
check_nop "A.u"

echo "passed: $OK/$TEST"
exit $KO
