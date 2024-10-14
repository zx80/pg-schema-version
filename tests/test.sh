#! /bin/bash

db=pg_schema_version_test
psv=pg-schema-version
pg=psql 

[ "$1" ] && psv="$1"

set -o pipefail

# counters
OK=0 KO=0 TEST=0

function check_que()
{
  local name="$1" number="$2" query="$3"
  shift 3
  let TEST+=1
  n=$($pg -tA -c "$query" $db)
  if [ "$n" -eq "$number" ] ; then
    let OK+=1
  else
    let KO+=1
    echo "KO: $name ($n vs $number)" 1>&2
  fi
}

function check_nop()
{
  local name="$1"
  shift 1
  check_que "nope $name" 0 "SELECT COUNT(*) FROM pg_catalog.pg_tables WHERE tablename='psv_app_status'"
}

function check_cnt()
{
  local name="$1" number="$2"
  shift 2
  check_que "count $name" "$number" "SELECT COUNT(DISTINCT app) FROM public.psv_app_status"
}

function check_ver()
{
  local name="$1" app="$2" version="$3"
  shift 3
  check_que "version $name" "$version" \
    "SELECT MAX(version) FROM public.psv_app_status WHERE app='$app'"
}

function check_psv()
{
  local name="$1" expect="$2" app="$3"
  shift 3
  let TEST+=1

  $psv -a "$app" "$@" > /dev/null
  result=$?

  if [ "$result" -eq "$expect" ] ; then
    let OK+=1
  else
    let KO+=1
    echo "KO: psv $name ($result vs $expect)" 1>&2
    return
  fi
}

function check_run()
{
  local name="$1" expect="$2" app="$3" cmd="$4"
  shift 4
  let TEST+=1

  [ "$cmd" ] && cmd="-v psv=$cmd"

  $psv -a "$app" "$@" | $pg $cmd $db
  result=$?

  if [ "$result" -eq "$expect" ] ; then
    let OK+=1
  else
    let KO+=1
    echo "KO: run $name $cmd ($result vs $expect)" 1>&2
    return
  fi
}

dropdb $db
createdb $db

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
check_run "1.1" 0 app "init"
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

# register dry/wet (note requires a prior init)
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
check_run "2.h" 0 app "remove:wet"
check_nop "2.i"

# create
check_nop "3.0"
check_run "3.1" 0 app "create"
check_run "3.2" 0 app "create:dry"
check_nop "3.3"
check_run "3.4" 0 app "create:wet"
check_cnt "3.5" 2
check_ver "3.6" app 0
check_run "3.7" 0 app "create:wet" bla_1.sql
check_ver "3.8" app 1
check_run "3.9" 0 app "create:wet" bla_1.sql bla_2.sql
check_ver "3.a" app 2
check_run "3.b" 0 app "create:wet" bla_1.sql bla_2.sql bla_3.sql
check_ver "3.c" app 3
check_run "3.d" 0 app "create:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql
check_ver "3.e" app 4
check_run "3.d" 0 app "remove:wet"
check_nop "3.g"

# create including error detection
check_nop "4.0"
check_run "4.1" 0 app "create"
check_run "4.2" 0 app "create:dry"
check_nop "4.3"
check_run "4.4" 0 app "create:wet"
check_cnt "4.5" 2
check_ver "4.6" psv 0
check_ver "4.7" app 0
check_run "4.8" 0 app "create:wet" bla_1.sql  # ok
check_ver "4.9" app 1
check_run "4.a" 0 app "create:wet" bla_2.sql bla_1.sql  # KO
check_run "4.b" 0 app "create:wet" bla_2.sql bla_3.sql  # KO
check_run "4.c" 0 app "create:wet" bla_2.sql bla_4.sql  # KO
check_ver "4.d" app 1
check_run "4.e" 0 app "create:wet" bla_1.sql bla_2.sql  # ok
check_ver "4.f" app 2
check_run "4.g" 0 app "create:wet" bla_1.sql bla_3.sql bla_2.sql  # KO
check_run "4.h" 0 app "create:wet" bla_1.sql bla_2.sql bla_2.sql  # KO
check_run "4.i" 0 app "create:wet" bla_1.sql bla_1.sql bla_2.sql  # KO
check_run "4.j" 0 app "create:wet" bla_1.sql bla_4.sql bla_2.sql bla_3.sql  # KO
check_ver "4.k" app 2
check_run "4.l" 0 app "create:wet" bla_1.sql bla_2.sql bla_3.sql  # ok
check_ver "4.m" app 3
check_run "4.n" 0 app "create:wet" bla_1.sql bla_2.sql bla_3.sql bla_4.sql  # ok
check_ver "4.o" app 4
check_run "4.p" 0 app "remove:wet"
check_nop "4.q"

# run
check_nop "5.0"
check_run "5.1" 0 app "run" bla_1.sql bla_2.sql
check_run "5.2" 0 app "run:dry" bla_1.sql bla_2.sql
check_nop "5.3"
check_run "5.4" 0 app "run:wet" bla_1.sql bla_2.sql  # KO, need init and register
check_nop "5.5"
check_run "5.6" 0 app "init:wet" bla_1.sql bla_2.sql
check_cnt "5.7" 1
check_run "5.8" 0 app "run:wet" bla_1.sql bla_2.sql  # KO, need register
check_cnt "5.9" 1
check_run "5.a" 0 app "register:wet" bla_1.sql bla_2.sql
check_cnt "5.b" 2
check_ver "5.c" app 0
check_run "5.d" 0 app "run:wet" bla_1.sql bla_2.sql
check_ver "5.e" app 2
check_run "5.f" 0 app "run:wet" bla_1.sql bla_3.sql bla_2.sql  # KO
check_ver "5.g" app 2
check_run "5.h" 0 app "remove:wet"
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

# help
check_run "7.0" 0 app "help"
check_run "7.1" 0 app "help:dry"
check_run "7.2" 0 app "help:wet"

# content errors and ignore
check_psv "bs command in script" 1 app bad_bs.sql
check_psv "bs command in script" 0 app -T bad_bs.sql
check_psv "sql command in script" 2 app bad_sql.sql
check_psv "sql command in script" 0 app -T bad_sql.sql

# various options
echo "-- bla 2 script" | check_psv "standard input" 0 app --debug bla_1.sql - bla_3.sql

$pg -c "CREATE SCHEMA psv_test_schema" $db
check_nop "8.0"
check_run "8.1" 0 bla "init:wet"   -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_run "8.2" 0 bla "remove:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_run "8.3" 0 bla "create:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
check_run "8.4" 0 bla "remove:wet" -s psv_test_schema -t psv_test_table bla_1.sql bla_2.sql bla_3.sql
$pg -c "DROP SCHEMA psv_test_schema" $db

rm -f tmp.out
check_psv "9.0 output option" 0 bla -o tmp.out bla_1.sql bla_2.sql
check_psv "9.1 output option" 3 bla -o tmp.out bla_1.sql bla_2.sql
rm -f tmp.out

dropdb $db

echo "passed: $OK/$TEST"
exit $KO
