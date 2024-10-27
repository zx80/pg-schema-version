#! /bin/bash

source psv-test-infra.sh

# infra dry/wet
check_nop "1.0"
check_run "1.1" 0 app "init" -v
check_nop "1.2"
check_run "1.3" 0 app "init:dry"
check_nop "1.4"
check_run "1.5" 0 app "create"
check_nop "1.6"
check_run "1.7" 0 app "create:dry"
check_nop "1.8"
check_run "1.9" 0 app "init:wet"
check_run "1.a" 0 app "init:wet"
check_cnt "1.b" 1
check_run "1.c" 0 app "remove:dry"
check_cnt "1.d" 1
check_run "1.e" 0 app "remove:wet"
check_nop "1.f"

echo "passed: $OK/$TEST"
exit $KO
