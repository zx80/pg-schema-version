#! /bin/bash
#
# psv test script
#
# Environment variables:
#
# - TEST_DB: test database (WILL BE dropped, recreated and dropped again).
# - TEST_PSV: psv command.
# - TEST_PSQL: psql command.
# - TEST_PG_OPTS: postgres command options for psql, createdb and dropdb.
# - TEST_STOP: stop on first error.

# override from the environment
db=${TEST_DB:-pg_schema_version_test}
psv=${TEST_PSV:-pg-schema-version}
psql=${TEST_PSQL:-psql}
pgopts=${TEST_PG_OPTS:-}

pg="$psql $pgopts"

set -o pipefail

# counters
OK=0 KO=0 TEST=0

# check result, update counters and report or raise errors
function test_result()
{
  local name="$1" val="$2" expect="$3"
  shift 3
  let TEST+=1
  if [ "$val" -eq "$expect" ] ; then
    let OK+=1
  else
    let KO+=1
    echo "KO: $TEST $name ($val vs $expect)" 1>&2
    [ "$TEST_STOP" ] && exit 1
  fi
}

# check an SQL query result
function check_que()
{
  local name="$1" number="$2" query="$3"
  shift 3
  n=$($pg -tA -c "$query" $db)
  test_result "$name" "$n" "$number"
}

# single quoting for SQL
function sq()
{
  local s="$1"
  echo ${s//\'/\\\'}
}

# check that there is no infra
function check_nop()
{
  local name="$1" table="${2:-psv_app_status}"
  shift 2
  table=$(sq "$table")
  check_que "nope $name" 0 "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE tablename='$table'"
}

# double quoting for Postgres SQL
function dq()
{
  local s="$1"
  echo ${s//\"/\\\"}
}

# check number of versioned applications
function check_cnt()
{
  local name="$1" number="$2" schema="${3:-public}" table="${4:-psv_app_status}"
  shift 4
  schema=$(dq "$schema") table=$(dq "$table")
  check_que "count $name" "$number" "SELECT COUNT(DISTINCT app) FROM \"$schema\".\"$table\" WHERE active"
}

# check current version of application
function check_ver()
{
  local name="$1" app="$2" version="$3" schema="${4:-public}" table="${5:-psv_app_status}"
  shift 5
  schema=$(dq "$schema") table=$(dq "$table")
  check_que "version $name" "$version" \
    "SELECT MAX(version) FROM \"$schema\".\"$table\" WHERE app='$app' AND active"
}

function check_des()
{
  local name="$1" app="$2" version="$3" description="$4"
  shift 4
  check_que "des $name" 1 \
    "SELECT COUNT(*) FROM public.psv_app_status
     WHERE app='$app' AND version=$version AND description='$description' AND active"
}

# run psv only
function check_psv()
{
  local name="$1" expect="$2" app="$3"
  shift 3

  [ "$app" ] && app="-a $app"

  $psv $app "$@" > /dev/null
  result=$?

  test_result "psv $name" "$result" "$expect"
}

# run psv and psql
function check_run()
{
  local name="$1" expect="$2" app="$3" cmd="$4"
  shift 4
  [ "$cmd" ] && cmd="-v psv=$cmd"

  local tmp=./tmp_$$.sql

  $psv -a "$app" "$@" > $tmp
  psv_result=$?
  test_result "run psv $name $cmd" $psv_result 0

  $pg $cmd $db < $tmp
  result=$?
  test_result "run pg $name $cmd" "$result" "$expect"

  rm -f $tmp
}

# empty test database
dropdb $pgopts $db
createdb $pgopts $db

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

# catchup
check_nop "7.0"
check_que "7.1" 0 "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE tablename = 'Foo'"
check_run "7.2" 0 foo "catchup" foo_1.sql
check_run "7.3" 0 foo "catchup:dry" foo_1.sql
check_nop "7.4"
check_run "7.5" 0 foo "catchup:wet" foo_1.sql
check_cnt "7.6" 2
check_ver "7.7" foo 1
check_run "7.8" 0 foo "catchup:wet" foo_1.sql foo_2.sql
check_ver "7.9" foo 2
check_run "7.a" 0 foo "catchup:wet" foo_1.sql foo_2.sql foo_3.sql
check_ver "7.b" foo 3
check_que "7.c" 0 "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE tablename = 'Foo'"
check_run "7.d" 0 app "remove:wet"
check_nop "7.e"

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
# NOTE unregister does a short exit without consumming all input
check_run "A.r" 0 bla "unregister:wet"
check_cnt "A.s" 1
check_run "A.t" 0 bla "remove:wet"
check_nop "A.u"

# cleanup test database
dropdb $pgopts $db

echo "passed: $OK/$TEST"
exit $KO
