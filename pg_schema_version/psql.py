APP_VERSION = r"""
\if :psv_no_infra
  \echo # psv skipping showing :psv_app version, no infra
\else
  --- show target app version if available
  SELECT MAX(version) AS psv_app_version
    FROM PsvAppStatus
    WHERE app = :'psv_app'
    \gset
  \if :{{?psv_app_version}}
    \echo # psv :psv_app version: :psv_app_version
    \unset psv_app_version
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
-- Run with extra care, after ensuring that you have a working backup.
--
-- example: psql -v psv=apply:dry -f {app}.sql
--
-- See: https://github.com/zx80/pg-schema-version
--
-- Control the script behavior by setting psql-variable "psv",
-- with the full format command:version:moisture.
--
-- Available commands: init, register, apply (default), create, status, unregister, remove, help, catchup.
-- Available moistures: dry (default), wet.
-- Version is the target version, default is latest.

-- any error will stop the script immediately
\set ON_ERROR_STOP 1

-- check postgres server version
SELECT :SERVER_VERSION_NUM < 100000 AS psv_pg_ko \gset
\if :psv_pg_ko
  \warn # ERROR psv requires postgres version 10 or above
  \quit
\endif
\unset psv_pg_ko

-- psv infra names
\set psv_schema {schema}
\set psv_table {table}

-- application name taken from scripts, but can be overriden with -v psv_app=…
\if :{{?psv_app}}
  \warn # WARN application name overriden to :psv_app
\else
  \set psv_app {app}
\endif
\echo # psv for application :psv_app

-- command to execute
\if :{{?psv}}
  -- psv set from command line
\else
  -- default command is to apply steps (no init nor register)
  \set psv apply:latest:dry
  \echo # psv set to :psv, change with -v psv=…
\endif

-- split command, version and moisture
SELECT
  CASE
    WHEN :'psv' ~ ':' THEN SPLIT_PART(:'psv', ':', 1)
    WHEN :'psv' IN ('dry', 'wet') THEN 'apply'
    ELSE :'psv'
  END AS psv_cmd,
  CASE
    WHEN :'psv' ~ ':\d+(:\w+)?$' THEN SPLIT_PART(:'psv', ':', 2)::INT
    WHEN :'psv' ~ ':latest(:\w+)?$' THEN -1
    ELSE -1 -- means latest
  END AS psv_cmd_version,
  CASE
    WHEN :'psv' ~ ':\d+:' THEN SPLIT_PART(:'psv', ':', 3)
    WHEN :'psv' ~ ':(dry|wet)$' THEN SPLIT_PART(:'psv', ':', -1)
    WHEN :'psv' IN ('dry', 'wet') THEN :'psv'
    ELSE 'dry'
  END AS psv_mst
  \gset

-- for display
SELECT
  CASE WHEN :psv_cmd_version = -1 THEN 'latest'
       ELSE (:psv_cmd_version)::TEXT
  END AS psv_cmd_version_display,
  current_database() AS psv_database
  \gset

-- set expected phases as booleans
SELECT

  -- check command validity
  :'psv_cmd' NOT IN ('init', 'register', 'apply',
      'create', 'status', 'unregister', 'remove',
      'help', 'catchup')                             AS psv_bad_cmd,

  -- whether to initialize the infra if needed
  :'psv_cmd' IN ('create', 'init', 'catchup')        AS psv_do_init,
  -- whether to register the application if needed
  :'psv_cmd' IN ('create', 'register', 'catchup')    AS psv_do_register,
  -- whether to unregister the application
  :'psv_cmd' IN ('unregister')                       AS psv_do_unregister,
  -- whether to show all application status
  :'psv_cmd' IN ('status')                           AS psv_do_status,
  -- whether to execute schema create steps
  :'psv_cmd' IN ('create', 'apply', 'catchup')       AS psv_do_apply,
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
  \warn # ERROR psv unexpected command :psv_cmd, expecting: init register apply create status remove help catchup
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
  \echo # use "-v psv=command:version:moisture" to control the script behavior.
  \echo #
  \echo # commands: init (create infra), register (add application to versioning system),
  \echo #   apply (execute needed schema steps, the default), status (show),
  \echo #   unregister (remove app from versioning system), remove (drop infra),
  \echo #   help (this help); create stands for init + register + apply.
  \echo #
  \echo # version: target version, default is latest.
  \echo #
  \echo # moistures: dry (default, just tell what will be done), wet (do it!).
  \echo #
  \echo # example: psql -v psv=create -f acme.sql
  \echo #
  \echo # documentation: https://zx80.github.com/pg-schema-version
  \quit
\endif

\if :psv_dry
  \echo # psv dry :psv_cmd for :psv_app on :psv_database, enable with -v psv=:psv_cmd::psv_cmd_version_display:wet
\else
  \echo # psv wet :psv_cmd for :psv_app on :psv_database
\endif

--
-- REMOVE
--
\if :psv_do_remove
  \if :psv_dry
    \echo # psv will drop its infra if it exists
  \else
    DROP TABLE IF EXISTS :"psv_schema".:"psv_table";
  \endif
  -- bye bye, nothing else to do!
  \quit
\endif

--
-- INIT create psv pristine infra if needed
--
SELECT COUNT(*) = 0 AS psv_no_infra
  FROM pg_catalog.pg_tables
  WHERE schemaname = :'psv_schema'
    AND tablename = :'psv_table'
  \gset

\if :psv_do_init
  \if :psv_no_infra
    \if :psv_dry
      -- output a precise message before quitting
      \if :psv_do_apply
         \if :psv_do_register
           \echo # psv will create infra, register :psv_app and execute all steps
         \else
           -- UNREACHABLE
           \warn # INTERNAL ERROR should not init and apply without registering
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
CREATE TABLE :"psv_schema".:"psv_table"(
  id SERIAL PRIMARY KEY,
  app TEXT NOT NULL DEFAULT 'psv',
  version INTEGER NOT NULL DEFAULT 0,
  signature TEXT DEFAULT NULL,
  filename TEXT DEFAULT NULL,
  description TEXT DEFAULT NULL,
  created TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(app, version),
  UNIQUE(signature),
  CHECK (version = 0 AND signature IS NULL OR version > 0 AND signature IS NOT NULL)
);

-- register itself
INSERT INTO :"psv_schema".:"psv_table" DEFAULT VALUES;

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
      \quit
    \else
      \warn # ERROR psv skipping needed psv infra initialization… consider commands init or create
      \quit
    \endif
  -- else there is an infra and we do not need to init
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

  WITH app_version AS (
    SELECT app, MAX(version) AS version
      FROM :"psv_schema".:"psv_table"
      GROUP BY 1)
  SELECT app, version, description
    FROM app_version
    JOIN :"psv_schema".:"psv_table" USING (app, version)
    ORDER BY 1;

\endif

--
-- setup dry run, changes are operated on a temporary copy
--
\if :psv_dry
  -- copy
  CREATE TEMPORARY TABLE PsvAppStatus
    AS SELECT * FROM :"psv_schema".:"psv_table";
\else
  -- reference
  CREATE TEMPORARY VIEW PsvAppStatus
    AS SELECT * FROM :"psv_schema".:"psv_table";
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
    \if :psv_do_apply
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
  -- nothing to do latter
  \quit
\endif

--
-- STEPS OR CATCHUP
--

-- check if nothing needs to be applied
SELECT :psv_cmd_version <> -1 AND COUNT(*) >= 1 AS psv_no_version_needed
  FROM PsvAppStatus
  WHERE app = :'psv_app'
    AND version >= :psv_cmd_version
    \gset

\if :psv_no_version_needed
  \echo # psv nothing to apply for target version :psv_cmd_version
  \quit
\endif

-- consider each step in turn
\if :psv_do_apply

  -- display helpers
  \if :psv_do_catchup
    \set psv_operating catching-up
  \else
    \set psv_operating applying
  \endif

  -- overall action summary
  \if :psv_dry
    \echo # psv will consider :psv_operating steps
  \else
    \echo # psv considering :psv_operating steps
  \endif
""" + APP_VERSION

FILE_HEADER = r"""
  --
  -- File {file}
  --
  -- check whether version is needed
  \set psv_filename {filename}
  \set psv_version {version}
  \set psv_signature {signature}
  \set psv_description {description}

  -- app schema previous upgrade was done
  SELECT COUNT(*) = 1 AS psv_version_previous_ok
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND version = :psv_version - 1
    \gset

  \if :psv_version_previous_ok
    -- app schema upgrade already applied
    SELECT COUNT(*) = 0 AS psv_version_needed
      FROM PsvAppStatus
      WHERE app = :'psv_app'
        AND version = :psv_version
      \gset
  \else
    \set psv_version_needed 0
  \endif
  \unset psv_version_previous_ok

  -- and below target
  \if :psv_version_needed
    SELECT :psv_cmd_version = -1 OR :psv_version <= :psv_cmd_version AS psv_version_needed
    \gset
    \if :psv_version_needed
      -- we are still on, let us proceed
    \else
      \if :psv_dry
        \echo # psv will skip :psv_app :psv_version (over :psv_cmd_version)
      \else
        \echo # psv skipping :psv_app :psv_version (over :psv_cmd_version)
      \endif
      \set psv_version_over_target 1
    \endif
  \endif

  \if :{{?psv_version_over_target}}
    -- skip these checks if skipping step because of the version target
    \set psv_version_inconsistent 0
    \set psv_version_used 0
  \else
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
  \endif

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
      INSERT INTO PsvAppStatus(app, version, signature, filename, description)
        VALUES (:'psv_app', :'psv_version', :'psv_signature', :'psv_filename', :'psv_description');
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
        INSERT INTO PsvAppStatus(app, version, signature, filename, description)
          VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description');
      \else
        \echo # psv applying :psv_app :psv_version

  BEGIN;
"""

FILE_FOOTER = r"""
    -- upgrade application new version
    INSERT INTO PsvAppStatus(app, version, signature, filename, description)
      VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description');

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
          SET signature = :'psv_signature',
              filename = :'filename'
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