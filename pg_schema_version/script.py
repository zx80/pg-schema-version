import os
import sys
import re
import logging
import argparse
from .utils import openfiles, bytes_hash, log

# NOTE this could be a postgres extension? NO, just one table.
# FIXME skipped begin/end keywords which interact with plpgsql…
# TODO description can replace signature? added?
# TODO verbose mode with log.info

APP_VERSION = r"""
\if :psv_no_infra
  \echo # psv skipping showing :psv_app version, no infra
\else
  --- show target app version if available
  SELECT MAX(version) AS psv_version
    FROM PsvAppStatus
    WHERE app = :'psv_app'
    \gset
  \if :{{?psv_version}}
    \echo # psv :psv_app version: :psv_version
    \unset psv_version
  \else
    \echo # psv :psv_app is not registered
  \endif
\endif
"""

SCRIPT_HEADER = r"""--
--      _ __  _____   __
--     | '_ \/ __\ \ / /
--     | |_) \__ \\ V /
--     | .__/|___/ \_/
--     |_|
--
-- AUTOMATICALLY GENERATED PSQL SCRIPT FOR APP {app}
--
-- This psql script has been generated by "pg-schema-version".
-- Edit with care, or possibly do not edit…
--
-- See: https://github.com/zx80/pg-schema-version
--
-- Control the script behavior by setting psql-variable "psv",
-- with the format command:moisture.
--
-- Available commands: init, register, run (default), create, status, unregister, remove, help, catchup.
-- Available moistures: dry (default), wet.

-- any error will stop the script immediately
\set ON_ERROR_STOP 1

-- check postgres server version
SELECT :SERVER_VERSION_NUM < 100000 AS psv_pg_ko \gset
\if :psv_pg_ko
  \warn # ERROR psv requires postgres version 10 or above
  \quit
\endif
\unset psv_pg_ko

-- application name
\set psv_app {app}

-- command to execute
\if :{{?psv}}
  -- nothing to do
\else
  -- default command is to run the script (no init nor register)
  \set psv run:dry
  \echo # psv set to :psv, change with -v psv=…
\endif

-- split command and moisture
SELECT
  CASE
    WHEN :'psv' ~ ':' THEN SPLIT_PART(:'psv', ':', 1)
    WHEN :'psv' IN ('dry', 'wet') THEN 'run'
    ELSE :'psv'
  END AS psv_cmd,
  CASE
    WHEN :'psv' ~ ':' THEN SPLIT_PART(:'psv', ':', 2)
    WHEN :'psv' IN ('dry', 'wet') THEN :'psv'
    ELSE 'dry'
  END AS psv_mst
  \gset

-- set expected phases as booleans
SELECT

  -- check command validity
  :'psv_cmd' NOT IN ('init', 'register', 'run',
      'create', 'status', 'unregister', 'remove',
      'help', 'catchup')                             AS psv_bad_cmd,

  -- whether to initialize the infra if needed
  :'psv_cmd' IN ('create', 'init', 'catchup')        AS psv_do_init,
  -- whether to register the application if needed
  :'psv_cmd' IN ('create', 'register', 'catchup')    AS psv_do_register,
  -- whether to unregister the application
  :'psv_cmd' IN ('unregister')                       AS psv_do_unregister,
  -- whether to show all application status
  TRUE                                               AS psv_do_status,
  -- whether to run schema create steps
  :'psv_cmd' IN ('create', 'run', 'catchup')         AS psv_do_steps,
  -- whether to remove the infrastructure
  :'psv_cmd' IN ('remove')                           AS psv_do_remove,
  -- whether to show help
  :'psv_cmd' IN ('help')                             AS psv_do_help,
  -- whether to catchup application versions
  :'psv_cmd' IN ('catchup')                          AS psv_do_catchup,

  -- check moisture validity
  :'psv_mst' NOT IN ('dry', 'wet')                   AS psv_bad_mst,

  -- dry run ?
  :'psv_mst' = 'dry'                                 AS psv_dry
  \gset

-- check that command is valid
\if :psv_bad_cmd
  \warn # ERROR psv unexpected command :psv_cmd, expecting: init register run create status remove
  \quit
\endif
\unset psv_bad_cmd
\if :psv_bad_mst
  \warn # ERROR psv unexpected moisture :psv_mst, expecting: dry wet
  \quit
\endif
\unset psv_bad_mst

-- show help, whether dry or wet!
\if :psv_do_help
  \echo # psql schema creation script for application {app}
  \echo # use "-v psv=command:moisture" to control the script behavior.
  \echo #
  \echo # commands: init (create infra), register (add application to versioning system),
  \echo #   run (apply needed schema steps, the default), status (show),
  \echo #   unregister (remove app from versioning system), remove (drop infra),
  \echo #   help (this help); create stands for init + register + run.
  \echo #
  \echo # moistures: dry (default, just tell what will be done), wet (do it!).
  \echo #
  \echo # example: psql -v psv=create -f acme.sql
  \echo #
  \echo # documentation: https://zx80.github.com/pg-schema-version
  \quit
\endif

\if :psv_dry
  \echo # psv dry :psv_cmd for :psv_app, enable with -v psv=:psv_cmd::wet
\else
  \echo # psv wet :psv_cmd for :psv_app
\endif

--
-- INIT create psv pristine infra if needed
--
SELECT COUNT(*) = 0 AS psv_no_infra
  FROM pg_catalog.pg_tables
  WHERE schemaname = '{schema}'
    AND tablename = '{table}'
  \gset

\if :psv_do_init
  \if :psv_no_infra
    \if :psv_dry
      -- output a precise message before quitting
      \if :psv_do_steps
         \if :psv_do_register
           \echo # psv will create infra, register :psv_app and execute all steps
         \else
           -- UNREACHABLE
           \warn # INTERNAL ERROR should not init and run without registering
           \quit
         \endif
      \else
         \if :psv_do_register
           \echo # psv will create infra and register :psv_app
         \else
           \echo # psv will create infra
         \endif
      \endif
      -- always quit without infra anyway
      \quit
    \else
      -- wet run, do the job!
      \echo # psv creating infra

BEGIN;

-- create psv application status table
CREATE TABLE {schema}.{table}(
  id SERIAL PRIMARY KEY,
  app TEXT NOT NULL DEFAULT 'psv',
  version INTEGER NOT NULL DEFAULT 0,
  signature TEXT DEFAULT NULL,
  created TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(app, version),
  UNIQUE(signature),
  CHECK (version = 0 AND signature IS NULL OR version > 0 AND signature IS NOT NULL)
);

-- register itself
INSERT INTO {schema}.{table} DEFAULT VALUES;

COMMIT;

      \set psv_no_infra 0
    \endif
  \else
    -- infra already exists
    \if :psv_dry
      \echo # psv will skip infra initialization
    \else
      \echo # psv skipping psv infra initialization
    \endif
  \endif
\else
  -- do not initialize
  \if :psv_no_infra
    \if :psv_dry
      \echo # psv will skip needed infra initialization… consider commands init or create
    \else
      \warn # psv skipping needed psv infra initialization… consider commands init or create
    \endif
  -- else there is an infra and we do not to init
  \endif
\endif

--
-- STATUS
--

\if :psv_do_status

  -- quit if infra is not available
  \if :psv_no_infra
    \if :psv_do_init
      -- ok, will have been initialized
      \if :psv_dry
        \echo # psv will show all application status
        -- nothing else to do
        \quit
      -- else proceed below
      \endif
    \else
      -- no infra and not initialized
      \warn # ERROR cannot show status without psv infra, consider commands init or create
      \quit
    \endif
  \endif

  -- show all app versions
  \echo # psv all applications status

  SELECT app, MAX(version) AS version
    FROM {schema}.{table}
    GROUP BY 1
    ORDER BY 1;

\endif

--
-- REMOVE psv infra
-- this is placed after STATUS so that the current status is shown
--
\if :psv_do_remove
  \if :psv_dry
    \echo # psv will drop its infra if it exists
  \else
    DROP TABLE IF EXISTS {schema}.{table};
  \endif
  -- nothing else to do
  \quit
\endif

--
-- setup dry run, changes are operated on a temporary copy
--
\if :psv_dry
  -- copy
  CREATE TEMPORARY TABLE PsvAppStatus
    AS SELECT * FROM {schema}.{table};
\else
  -- reference
  CREATE TEMPORARY VIEW PsvAppStatus
    AS SELECT * FROM {schema}.{table};
\endif

-- self check for possible future upgrades
SELECT MAX(version) <> 0 AS psv_not_v0
  FROM PsvAppStatus
  WHERE app = 'psv'
  \gset

\if :psv_not_v0
  \warn # ERROR unexpected psv version
  \quit
\endif

-- check that the application is known
SELECT COUNT(*) = 0 AS psv_app_ko
  FROM PsvAppStatus
  WHERE app = :'psv_app'
  \gset

--
-- REGISTER
--

\if :psv_do_register
  \if :psv_app_ko
    \if :psv_dry
      \echo # psv will register :psv_app
    \else
      \echo # psv registering :psv_app
    \endif
    -- actually register, possibly on the copy for the dry run
    INSERT INTO PsvAppStatus(app) VALUES (:'psv_app');
  \else
    \echo # psv skipping unneeded :psv_app registration
  \endif
\else
  \if :psv_app_ko
    \if :psv_do_steps
      \warn # ERROR :psv_app registration needed
      \quit
    -- else it will not be needed
    \endif
  \endif
  \if :psv_dry
    \echo # psv will skip :psv_app registration
  \else
    \echo # psv skipping :psv_app registration
  \endif
\endif

--
-- UNREGISTER
--

\if :psv_do_unregister
  \if :psv_app_ko
    \if :psv_dry
      \echo # psv will skip unregistering unregistered :psv_app
    \else
      \echo # psv skipping unregistering unregistered :psv_app
    \endif
  \else
    \if :psv_dry
      \echo # psv will unregister :psv_app
    \else
      \echo # psv unregistering :psv_app
      DELETE FROM PsvAppStatus WHERE app = :'psv_app';
    \endif
  \endif
\endif

--
-- STEPS OR CATCHUP
--

-- consider each step in turn
\if :psv_do_steps

  -- display helpers
  \if :psv_do_catchup
    \set psv_operating catching-up
  \else
    \set psv_operating applying
  \endif

  -- overall action summary
  \if :psv_dry
    \echo # psv will consider :psv_operating all steps
  \else
    \echo # psv considering :psv_operating all steps
  \endif
""" + APP_VERSION

FILE_HEADER = r"""
  --
  -- File {file}
  --
  -- check whether version is needed
  \set psv_version {version}
  \set psv_signature {signature}

  -- app schema upgrade already applied
  SELECT COUNT(*) = 0 AS psv_version_needed
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND version = :psv_version
    \gset

  -- app schema upgrade already applied with another script
  SELECT COUNT(*) = 0 AS psv_version_inconsistent
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND version = :psv_version
      AND signature = :'psv_signature'
    \gset

  -- this script was used somewhere already
  SELECT COUNT(*) > 0 AS psv_signature_used
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND signature = :'psv_signature'
    \gset

  \if :psv_version_needed
    -- app version to be applied
    \if :psv_do_catchup
      \if :psv_dry
        \echo # psv will catch-up :psv_app :psv_version
      \else
        \echo # psv catching-up :psv_app :psv_version
      \endif
      \if :psv_signature_used
        -- will fail on UNIQUE(signature)
        \warn # ERROR :psv_app :psv_version script already applied
        \quit
      \endif
      -- do it anyway, possibly on the fake copy ?
      INSERT INTO PsvAppStatus(app, version, signature)
        VALUES (:'psv_app', :'psv_version', :'psv_signature');
    \else
      -- actual execution mode!
      \if :psv_signature_used
        -- will fail on UNIQUE(signature)
        \warn # ERROR :psv_app :psv_version script already applied
        \quit
      \endif

      \if :psv_dry
        \echo # psv will apply :psv_app :psv_version
        -- upgrade application new version for dry run, on the tmp table
        INSERT INTO PsvAppStatus(app, version, signature)
          VALUES (:'psv_app', :psv_version, :'psv_signature');
      \else
        \echo # applying :psv_app :psv_version

  BEGIN;
"""

FILE_FOOTER = r"""
    -- upgrade application new version
    INSERT INTO PsvAppStatus(app, version, signature)
      VALUES (:'psv_app', :psv_version, :'psv_signature');

  COMMIT;

      \endif
    \endif
  \else
    -- step not needed
    \if :psv_version_inconsistent
      \if :psv_do_catchup
        \warn # WARN :psv_app :psv_version inconsistent signature
        \if :psv_signature_used
          \echo # ERROR cannot update :psv_app :psv_version, signature collision
          \quit
        \endif
        \if :psv_dry
          \echo # psv will update signature
        \else
          \echo # psv updating signature
        \endif
        UPDATE PsvAppStatus
          SET signature = :'psv_signature'
          WHERE app = :'pvs_app'
            AND version = :'psv_version';
      \else
        \warn # ERROR :psv_app :psv_version inconsistent signature
        \quit
      \endif
    \endif
    \if :psv_dry
      \echo # psv will skip :psv_app :psv_version
    \else
      \echo # psv skipping :psv_app :psv_version
    \endif
  \endif

  \unset psv_version
  \unset psv_signature
"""

SCRIPT_FOOTER = APP_VERSION + r"""
\else
  -- do not apply steps
  \if :psv_dry
    \echo # psv will skip all schema steps for command :psv_cmd
  \else
    \echo # psv skipping all schema steps for command :psv_cmd
  \endif
\endif

-- final output
\if :psv_dry
  DROP TABLE PsvAppStatus;
  \echo # psv dry :psv_cmd for :psv_app done
\else
  DROP VIEW PsvAppStatus;
  \echo # psv wet :psv_cmd for :psv_app done
\endif

-- end of {app} psv script
"""

def gen_psql_script(args):
    """Generate an idempotent psql script."""

    def output(s: str):
        print(s, file=args.out, end="")

    output(SCRIPT_HEADER.format(app=args.app, schema=args.schema, table=args.table))

    version = 0
    for fn, fh in openfiles(args.sql):
        version += 1
        script = fh.read()
        # sanity checks
        if re.search(r"^\s*\\", script, re.M):
            if args.trust_scripts:
                log.warning(f"script {fn} seems to contain a backslash command")
            else:
                log.error(f"script {fn} contains a backslash command")
                return 1
        if re.search(r"^\s*(commit|rollback|savepoint)\b", script, re.I|re.M):
            if args.trust_scripts:
                log.warning(f"script {fn} seems to contain a transaction command")
            else:
                log.error(f"script {fn} contains a transaction command")
                return 2
        data = script.encode(args.encoding)
        signature = bytes_hash(args.hash, data)
        # output psql code
        output(FILE_HEADER.format(file=fn, version=version, signature=signature))
        output(script)
        output(FILE_FOOTER)

    output(SCRIPT_FOOTER.format(app=args.app, schema=args.schema, table=args.table))

    return 0

def psv():

    logging.basicConfig()

    ap = argparse.ArgumentParser(
            prog="pg-schema-version",
            description="Generate an idempotent psql script for Postgres schema versioning.",
            epilog="All software have bugs…")
    ap.add_argument("-d", "--debug", action="store_true",
                    help="debug mode")
    ap.add_argument("-a", "--app", type=str, default="app",
                    help="application name, default is 'app'")
    ap.add_argument("-s", "--schema", type=str, default="public",
                    help="schema for psv infra, default is 'public'")
    ap.add_argument("-t", "--table", type=str, default="psv_app_status",
                    help="psv table name, default is 'psv_app_status'")
    ap.add_argument("-e", "--encoding", type=str, default="UTF-8",
                    help="sql file encoding, default is 'UTF-8'")
    ap.add_argument("-H", "--hash", type=str, default="sha3_256",
                    help="hashlib algorithm for step signature, default is 'SHA3-256'")
    ap.add_argument("-o", "--out", type=str, default=sys.stdout,
                    help="output script, default on stdout")
    ap.add_argument("-T", "--trust-scripts", action="store_true",
                    help="blindly trust provided scripts")
    ap.add_argument("sql", nargs="*",
                    help="sql data definition files")
    args = ap.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    if isinstance(args.out, str):
        if os.path.exists(args.out):
            log.error(f"psv will not overwrite output file {args.out}, remove it first")
            return 3
        args.out = open(args.out, "w")

    return gen_psql_script(args)
