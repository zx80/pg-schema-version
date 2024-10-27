#! /bin/bash

source psv-test-infra.sh

# various options and behavior
$pg -c "CREATE SCHEMA psv_test_schema" $db
check_nop "8.0"
check_nop "8.1" psv_test_schema psv_test_table
check_run "8.2" 0 bla "init:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_cnt "8.3" 1 psv_test_schema psv_test_table
check_run "8.4" 0 bla "register:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_cnt "8.5" 2 psv_test_schema psv_test_table
check_ver "8.6" psv 0 psv_test_schema psv_test_table
check_ver "8.7" bla 0 psv_test_schema psv_test_table
check_run "8.8" 0 bla "remove:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_nop "8.9" psv_test_schema psv_test_table
check_run "8.a" 0 bla "create:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_cnt "8.b" 2 psv_test_schema psv_test_table
check_ver "8.c" bla 3 psv_test_schema psv_test_table
check_run "8.d" 0 bla "remove:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_nop "8.e" psv_test_schema psv_test_table
# more fantasy
check_run "8.f" 0 bla "create:wet" -s psv_test_schema -t "let's run versions" bla_1.sql bla_2.sql
check_cnt "8.g" 2 psv_test_schema "let's run versions"
check_ver "8.h" bla 2 psv_test_schema "let's run versions"
check_run "8.i" 0 bla "remove:wet" -s psv_test_schema -t "let's run versions"
check_nop "8.j" psv_test_schema "let's run versions"
check_nop "8.k"
$pg -c "DROP SCHEMA psv_test_schema" $db

# content errors and ignore
check_psv "8.l bs command in script" 4 bad bad_bs.sql
check_psv "8.m bs command in script" 0 bad -T bad_bs.sql
check_psv "8.n sql command in script" 5 bad bad_sql.sql
check_psv "8.o sql command in script" 0 bad -T -p bad_sql.sql
check_psv "8.p no psv header" 2 bad -p bad_psv.sql
check_psv "8.q malformed psv header" 3 bad bad_psv2.sql
check_psv "8.r zero version" 6 bad bad_zero.sql
check_psv "8.s repeated" 7 bla bla_1.sql bla_1.sql
check_psv "8.t infered name" 0 "" bla_1.sql bla_2.sql bla_3.sql
check_psv "8.u" 8 bla bla_4.sql bla_2.sql bla_1.sql
check_psv "8.v" 0 bla -p bla_4.sql bla_2.sql bla_1.sql
check_psv "8.w" 9 app bla_4.sql bla_3.sql bla_2.sql bla_1.sql
check_psv "8.x" 10 bla bla_m1.sql bla_m2.sql bla_m3.sql
check_psv "8.y" 0 bla -p bla_m1.sql bla_m2.sql bla_m3.sql
check_psv "8.z" 0 bla bla_1.sql bla_2.sql bla_m1.sql bla_m2.sql
check_psv "8.A" 10 bla bla_1.sql bla_2.sql bla_3.sql bla_m1.sql bla_m2.sql
check_psv "8.B" 0 bla -p bla_1.sql bla_2.sql bla_3.sql bla_m1.sql bla_m2.sql
check_psv "8.C" 10 bla bla_1.sql bla_2.sql bla_m1.sql bla_m2.sql bla_m3.sql
check_psv "8.D" 0 bla -p bla_1.sql bla_2.sql bla_m1.sql bla_m2.sql bla_m3.sql

# output overwrite
rm -f tmp.out
check_psv "8.E output option" 0 bla -o tmp.out bla_1.sql bla_2.sql
check_psv "8.F output option" 1 bla -o tmp.out bla_1.sql bla_2.sql
rm -f tmp.out

# help
check_run "8.G" 0 app "help"
check_run "8.H" 0 app "help:dry"
check_run "8.I" 0 app "help:wet"

# stdin
check_psv "8.J standard input" 0 bla --debug bla_1.sql - bla_3.sql <<EOF
-- psv: bla +2
EOF

# trigger a repeated error under debug
check_psv "8.K error under debug" 1 bla --debug bla_1.sql bla_2.sql bla_1.sql 2> /dev/null
check_psv "8.L version" 0 bla --version
check_psv "8.M app" 1 "<bad-name>"
check_psv "8.N hash" 1 bla --hash "no-such-algorithm" bla_1.sql

echo "passed: $OK/$TEST"
exit $KO
