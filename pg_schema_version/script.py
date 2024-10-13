import logging
import argparse
import sys
from .utils import openfiles, bytes_hash, log

# NOTE this could be a postgres extension?
# TODO do not rely on search path?
# TODO warn about explicit transactions
# TODO warn about backslash commands
# TODO drop option
# TODO create option? no-create option? command?
# TODO description can replace signature? added?
# TODO out option
# FIXME how to really stop on errors?

APP_VERSION = r"""
--- show app version
SELECT MAX(version) AS psv_version
  FROM PsvAppStatus
  WHERE app = :'psv_app'
  \gset
\echo # :psv_app version: :psv_version
"""

INITIAL_HEADER = r"""--
-- DO NOT EDIT
--
-- This psql script has been generated by "pg-schema-version"
-- See: https://github.com/zx80/pg-schema-version
--
"""

DROP_INFRA = r"""
-- drop psv infrastructure
DROP TABLE IF EXISTS psv_app_status CASCADE;
"""

SCRIPT_HEADER = r"""
\set STOP_ON_ERROR 1
\set psv_app {app}

-- check postgres server version
SELECT :SERVER_VERSION_NUM < 100000 AS psv_pg_ko \gset
\if :psv_pg_ko
  \echo # psv requires pg version 10 or above
  \! kill $PPID
  \quit
\endif

-- set psv_dry_run
\if :{{?psv_wet_run}}
  \echo # psv wet run for :psv_app
  \set psv_dry_run 0
\else
  \echo # psv dry run for :psv_app, enable with -v psv_wet_run=1
  \set psv_dry_run 1
\endif

--
-- create psv infrastructure if necessary
--

SELECT COUNT(*) = 0 AS psv_no_infra
  FROM pg_tables
  WHERE tablename = 'psv_app_status' \gset

\if :psv_no_infra
  \if :psv_dry_run
    \echo # psv will create infrastructure and execute all commands
    \! kill $PPID
    \quit
  \else
    \echo # creating PSV infrastructure

BEGIN;
CREATE TABLE PUBLIC.psv_app_status(
  id SERIAL PRIMARY KEY,
  app TEXT NOT NULL DEFAULT 'psv',
  version INTEGER NOT NULL DEFAULT 0,
  signature TEXT DEFAULT NULL,
  created TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(app, version),
  UNIQUE(signature),
  CHECK (version = 0 AND signature IS NULL OR version > 0 AND signature IS NOT NULL)
);
INSERT INTO PUBLIC.psv_app_status DEFAULT VALUES;
INSERT INTO PUBLIC.psv_app_status(app) VALUES (:'psv_app');
COMMIT;

  \endif
\endif

-- dry run changes are operated on a temporary copy
\if :psv_dry_run
  -- copy
  CREATE TEMPORARY TABLE PsvAppStatus
    AS SELECT * FROM PUBLIC.psv_app_status;
\else
  -- reference
  CREATE TEMPORARY VIEW PsvAppStatus
    AS SELECT * FROM PUBLIC.psv_app_status;
\endif

-- self check
SELECT COUNT(*) <> 1 AS psv_not_v0
  FROM PsvAppStatus
  WHERE app = 'psv'
  \gset

\if :psv_not_v0
  \echo # psv: unknown version
  \! kill $PPID
  \quit
\endif

-- check that the application is known
SELECT COUNT(*) = 0 AS psv_app_ko
  FROM PsvAppStatus
  WHERE app = :'psv_app'
  \gset

\if :psv_app_ko
  \if :{{?psv_force_app}}
    INSERT INTO PsvAppStatus(app) VALUES (:'psv_app');
  \else
    \echo # ERROR application :psv_app is unknown, force addition with -v psv_force_app=1
    \! kill $PPID
    \quit
  \endif
\endif
""" + APP_VERSION

FILE_HEADER = r"""
--
-- File {file}
--
-- check whether version is needed
\set psv_version {version}
\set psv_signature {signature}

SELECT COUNT(*) = 0 AS psv_version_needed
  FROM PsvAppStatus
  WHERE app = :'psv_app'
    AND version = :psv_version
  \gset

SELECT COUNT(*) = 0 AS psv_version_inconsistent
  FROM PsvAppStatus
  WHERE app = :'psv_app'
    AND version = :psv_version
    AND signature = :'psv_signature'
  \gset

SELECT COUNT(*) > 0 AS psv_signature_used
  FROM PsvAppStatus
  WHERE app = :'psv_app'
    AND signature = :'psv_signature'
  \gset

\if :psv_version_needed
  \if :psv_signature_used
    \echo # ERROR :psv_app :psv_version signature already used
    \! kill $PPID
    \quit
  \endif
  \if :psv_dry_run
    \echo # psv will apply :psv_app :psv_version
  \else
    \echo # applying :psv_app :psv_version
BEGIN;
  INSERT INTO PsvAppStatus(app, version, signature)
    VALUES (:'psv_app', :psv_version, :'psv_signature');
"""

FILE_FOOTER = r"""
COMMIT;
    -- stop on any errors
    SELECT :LAST_ERROR_SQLSTATE <> '00000' AS psv_script_error \gset
    \if :psv_script_error
      \echo # ERROR: aborting on :psv_name :psv_version
      \! kill $PPID
      \quit
    \endif
  \endif
\else
  \if :psv_version_inconsistent
    \echo # ERROR :psv_app :psv_version inconsistent signature
    \! kill $PPID
    \quit
  \endif
  \if :psv_dry_run
    \echo # psv will skip :psv_app :psv_version
  \else
    \echo # skipping :psv_app :psv_version
  \endif
\endif
"""

SCRIPT_FOOTER = r"""
\if :psv_dry_run
  \echo # psv dry run done
  DROP TABLE PsvAppStatus;
\else
""" + APP_VERSION + r"""
  DROP VIEW PsvAppStatus;
\endif
"""

def gen_psql_script(args):
    """Generate an idempotent psql script."""

    if args.debug:
        log.setLevel(logging.DEBUG)

    print(INITIAL_HEADER)
    print(SCRIPT_HEADER.format(app=args.app))
    version = 0
    for fn, fh in openfiles(args.sql):
        version += 1
        script = fh.read()
        signature = bytes_hash(args.hash, script, args.encoding)
        print(FILE_HEADER.format(file=fn, version=version, signature=signature))
        print(script)
        print(FILE_FOOTER)
    print(SCRIPT_FOOTER)

    return 0

def psv():

    logging.basicConfig()

    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--debug", help="debug mode", action="store_true")
    ap.add_argument("-a", "--app", help="application name", type=str, default="app")
    ap.add_argument("-e", "--encoding", help="sql file encoding", type=str, default="UTF-8")
    ap.add_argument("--hash", help="hash algorithm", type=str, default="sha3_256")
    ap.add_argument("--drop", help="drop infrastructure", action="store_true")
    ap.add_argument("sql", help="sql data definition files, defaults to stdin", nargs="*")
    args = ap.parse_args()

    if args.drop:
        print(INITIAL_HEADER)
        print(DROP_INFRA)
        return 0
    else:
        return gen_psql_script(args)
