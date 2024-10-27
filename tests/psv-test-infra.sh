#
# psv test script infrastructure
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
