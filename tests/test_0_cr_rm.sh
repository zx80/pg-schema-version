#! /bin/bash

source psv-test-infra.sh

# create and remove the infra
check_nop "0.0"
check_run "0.1" 0 app "init:wet"
check_cnt "0.2" 1
check_ver "0.3" psv 0 
check_run "0.4" 0 app "init:wet"
check_cnt "0.5" 1
check_ver "0.6" psv 0 
check_run "0.7" 0 app "remove"
check_run "0.8" 0 app "remove:dry"
check_ver "0.9" psv 0 
check_run "0.a" 0 app "remove:wet"
check_run "0.b" 0 app "remove:wet"
check_nop "0.c"

echo "passed: $OK/$TEST"
exit $KO
