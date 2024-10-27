#! /bin/bash

source psv-test-infra.sh

# register/unregister dry/wet (note requires a prior init)
check_nop "2.0"
check_run "2.1" 0 app "register"
check_nop "2.2"
check_run "2.3" 0 app "register:dry"
check_nop "2.4"
check_run "2.5" 0 app "init:wet"
check_cnt "2.6" 1
check_run "2.7" 0 app "register:wet"
check_ver "2.8" psv 0
check_ver "2.9" app 0
check_cnt "2.a" 2
check_run "2.b" 0 foo "register:wet"
check_cnt "2.c" 3
check_ver "2.d" foo 0
check_run "2.e" 0 bla "register:wet"
check_cnt "2.f" 4
check_ver "2.g" bla 0
check_run "2.h" 0 bla "unregister"
check_run "2.i" 0 bla "unregister:dry"
check_cnt "2.j" 4
check_run "2.k" 0 bla "unregister:wet"
check_cnt "2.m" 3
check_run "2.n" 0 foo "unregister:wet"
check_cnt "2.o" 2
check_run "2.p" 0 app "unregister:wet"
check_cnt "2.q" 1
check_run "2.r" 0 app "register:wet"
check_cnt "2.s" 2
check_ver "2.t" app 0
check_run "2.u" 0 app "remove:wet"
check_nop "2.v"

echo "passed: $OK/$TEST"
exit $KO
