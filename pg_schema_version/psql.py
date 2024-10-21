# psql script parts for psv
# programming with "if boolean_variable" without logical operators is so fun!

APP_VERSION = r"""
\if :psv_no_infra
  \echo # psv skipping showing :psv_app version, no infra
\else
  --- show target app version if available
  SELECT MAX(version) AS psv_app_version
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND active
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
-- Available commands: init, register, apply (default), create, status, history, unregister, remove, help, catchup.
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

-- debugging output
\if :{{?psv_debug}}
  -- debug is set
\else
  \set psv_debug 0
\endif

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
    WHEN :'psv' ~ '^[a-z]+(:(\d+|latest))?(:(dry|wet))?$' THEN FALSE
    WHEN :'psv' ~ '^(\d+|latest)(:(dry|wet))?$' THEN FALSE
    WHEN :'psv' ~ '^(dry|wet)$' THEN FALSE
    ELSE TRUE
  END AS psv_cmd_ko,
  CASE
    WHEN :'psv' ~ '^(\d+|latest)(:(dry|wet))?$' THEN 'apply'
    WHEN :'psv' ~ '^(dry|wet)$' THEN 'apply'
    WHEN :'psv' ~ ':' THEN SPLIT_PART(:'psv', ':', 1)
    ELSE :'psv'
  END AS psv_cmd,
  CASE
    WHEN :'psv' ~ ':\d+:?' THEN SPLIT_PART(:'psv', ':', 2)::INT
    WHEN :'psv' ~ '\d+:?' THEN SPLIT_PART(:'psv', ':', 1)::INT
    WHEN :'psv' ~ 'latest' THEN -1
    ELSE -1 -- means latest
  END AS psv_cmd_version,
  CASE
    WHEN :'psv' ~ ':dry$' THEN 'dry'
    WHEN :'psv' ~ ':wet$' THEN 'wet'
    WHEN :'psv' ~ '^(dry|wet)$' THEN :'psv'
    ELSE 'dry'
  END AS psv_mst
  \gset

\if :psv_cmd_ko
  \echo # ERROR unexpected psv setting: :psv
  \quit
\endif

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
      'reverse', 'create', 'status', 'help', 'history',
      'unregister', 'remove', 'catchup')                   AS psv_bad_cmd,

  -- whether to initialize the infra if needed
  :'psv_cmd' IN ('create', 'init', 'catchup')              AS psv_do_init,
  -- whether to register the application if needed
  :'psv_cmd' IN ('create', 'register', 'catchup')          AS psv_do_register,
  -- whether to unregister the application
  :'psv_cmd' IN ('unregister')                             AS psv_do_unregister,
  -- whether to show all application status
  :'psv_cmd' IN ('status')                                 AS psv_do_status,
  -- whether to show application history
  :'psv_cmd' IN ('history')                                AS psv_do_history,
  -- whether to execute any step
  :'psv_cmd' IN ('create', 'apply', 'catchup', 'reverse')  AS psv_do_steps,
  -- whether to execute forward steps
  :'psv_cmd' IN ('create', 'apply')                        AS psv_do_apply,
  -- whether to catchup application versions
  :'psv_cmd' IN ('catchup')                                AS psv_do_catchup,
  -- whether to execute backward steps
  :'psv_cmd' IN ('reverse')                                AS psv_do_reverse,
  -- whether to remove the infrastructure
  :'psv_cmd' IN ('remove')                                 AS psv_do_remove,
  -- whether to show help
  :'psv_cmd' IN ('help')                                   AS psv_do_help,

  -- check moisture validity
  :'psv_mst' NOT IN ('dry', 'wet')                         AS psv_bad_mst,

  -- dry run ?
  :'psv_mst' = 'dry'                                       AS psv_dry
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
  \echo #   apply (execute needed forward steps, the default), status (show),
  \echo #   reverse (execute backward steps), unregister (remove app from versioning system),
  \echo #   remove (drop infra), help (this help); create stands for init + register + apply.
  \echo #
  \echo # version: target version, default is latest.
  \echo #
  \echo # moistures: dry (default, just tell what will be done), wet (do it!).
  \echo #
  \echo # example: psql -v psv=create -f acme.sql
  \echo #
  \echo # documentation: https://zx80.github.io/pg-schema-version
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

  \if :psv_debug
    \echo # DEBUG - REMOVE
  \endif

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

  \if :psv_debug
    \echo # DEBUG - INIT
  \endif

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

        SELECT
          :'psv_table' || '_av' AS psv_idx_av,
          :'psv_table' || '_s' AS psv_idx_s
          \gset

        -- create psv application status table
        CREATE TABLE :"psv_schema".:"psv_table"(
          id SERIAL PRIMARY KEY,
          app TEXT NOT NULL DEFAULT 'psv',
          version INTEGER NOT NULL DEFAULT 0,
          signature TEXT DEFAULT NULL,
          filename TEXT DEFAULT NULL,
          description TEXT DEFAULT NULL,
          username TEXT NOT NULL DEFAULT SESSION_USER,
          command TEXT NOT NULL DEFAULT 'bootstrap',
          created TIMESTAMP NOT NULL DEFAULT NOW(),
          active BOOLEAN NOT NULL DEFAULT TRUE,
          CHECK (version = 0 AND signature IS NULL OR
                 version > 0 AND signature IS NOT NULL)
        );

        CREATE UNIQUE INDEX :"psv_idx_av"
          ON :"psv_schema".:"psv_table"(app, version)
          WHERE active;

        CREATE UNIQUE INDEX :"psv_idx_s"
          ON :"psv_schema".:"psv_table"(signature)
          WHERE active;

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

  \if :psv_debug
    \echo # DEBUG - STATUS
  \endif

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
      WHERE active
      GROUP BY 1)
  SELECT app, version, description
    FROM app_version
    JOIN :"psv_schema".:"psv_table" USING (app, version)
    WHERE active
    ORDER BY 1;
  \quit

\endif

--
-- HISTORY
--

\if :psv_do_history

  \if :psv_debug
    \echo # DEBUG - HISTORY
  \endif

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
      \warn # ERROR cannot show history without psv infra, consider commands init or create
      \quit
    \endif
  \endif

  -- show all app versions
  \echo # psv application :psv_app history

  SELECT app, version, command, active, created
    FROM :"psv_schema".:"psv_table"
    WHERE app = :'psv_app'
    ORDER BY 5 DESC;
  \quit

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
    AND active
  \gset

\if :psv_not_v0
  \warn # ERROR unexpected psv version
  \quit
\endif

-- check if the application is unknown
SELECT COUNT(*) = 0 AS psv_app_ko
  FROM PsvAppStatus
  WHERE app = :'psv_app'
    AND active
  \gset

--
-- REGISTER
--

\if :psv_do_register

  \if :psv_debug
    \echo # DEBUG - REGISTER
  \endif

  \if :psv_app_ko
    \if :psv_dry
      \echo # psv will register :psv_app
    \else
      \echo # psv registering :psv_app
    \endif
    -- actually register, possibly on the copy for the dry run
    INSERT INTO PsvAppStatus(app, command)
      VALUES (:'psv_app', :'psv_cmd');
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

  \if :psv_debug
    \echo # DEBUG - UNREGISTER
  \endif

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
      BEGIN;
        UPDATE PsvAppStatus
          SET active = FALSE
          WHERE app = :'psv_app'
            AND active;
        INSERT INTO PsvAppStatus(app, command, active)
          VALUES (:'psv_app', :'psv_cmd', FALSE);
      COMMIT;
    \endif
  \endif
  -- nothing to do latter anyway
  \quit
\endif

--
-- STEPS (APPLY or REVERSE) or CATCHUP
--

-- check if nothing needs to be executed
-- set display helpers in passing
\if :psv_do_apply

  SELECT :psv_cmd_version <> -1 AND COUNT(*) >= 1 AS psv_no_step_needed
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND version >= :psv_cmd_version
      AND active
    \gset
  \set psv_operating applying
  \set psv_operate apply

\elif :psv_do_reverse

  SELECT COUNT(*) = 0 AS psv_no_step_needed
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND version > :psv_cmd_version
      AND active
    \gset
  \set psv_operating reversing
  \set psv_operate reverse

\elif :psv_do_catchup

  \set psv_no_step_needed 0
  \set psv_operating catching-up
  \set psv_operate catch-up
  -- NOTE catch-up will always check forward steps, eg to update signatures
  SELECT COUNT(*) AS psv_catchup_removals,
         COUNT(*) > 0 AS psv_has_catchup_removals
    FROM PsvAppStatus
    WHERE app = :'psv_app'
      AND :psv_cmd_version <> -1
      AND version > :psv_cmd_version
      AND active
    \gset

  \if :psv_has_catchup_removals
    \if :psv_dry
      \echo # psv :psv_operate will downgrade :psv_catchup_removals steps
    \else
      \echo # psv :psv_operate downgrading :psv_catchup_removals steps
    \endif
    -- do it anyway, possibly on the tmp copy
    BEGIN;
      UPDATE PsvAppStatus
        SET active = FALSE
        WHERE app = :'psv_app'
          AND version > :psv_cmd_version
          AND active;
      INSERT INTO PsvAppStatus(app, command, version, active)
        VALUES (:'psv_app', :'psv_cmd', :psv_version, FALSE);
    COMMIT;
  \endif

\else

  \set psv_no_step_needed 1
  \set psv_operating doing
  \set psv_operate do
\endif

\if :psv_no_step_needed
  \echo # psv nothing to :psv_operate for :psv_app target version :psv_cmd_version_display
  \quit
\endif

-- psv_do_apply_catchup := psv_do_apply OR psv_do_catchup
\set psv_do_apply_catchup 0
\if :psv_do_apply
  \set psv_do_apply_catchup 1
\endif
\if :psv_do_catchup
  \set psv_do_apply_catchup 1
\endif

-- consider each step in turn
\if :psv_do_steps

  \if :psv_debug
    \echo # DEBUG - STEPS
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
  \set psv_forward {forward}
  \set psv_operation {operation}

  \if :psv_debug
    \echo # DEBUG - STEP :psv_app :psv_operation :psv_version
    SELECT app, version, command, active, signature
      FROM PsvAppStatus WHERE app = :'psv_app' ORDER BY created DESC;
  \endif

  -- first consider step direction to know if we should consider this
  \if :psv_forward
    \if :psv_do_apply_catchup
      \set psv_keep_step 1
    \else
      \set psv_keep_step 0
    \endif
  \else
    -- backward
    \if :psv_do_reverse
      \set psv_keep_step 1
    \else
      \set psv_keep_step 0
    \endif
  \endif

  \if :psv_debug
    \echo # DEBUG :psv_app :psv_operation :psv_version considered: :psv_keep_step
  \endif

  \if :psv_keep_step

    -- precondition : app schema prior operation was done
    \if :psv_do_apply_catchup
      SELECT COUNT(*) = 1 AS psv_version_prec
        FROM PsvAppStatus
        WHERE app = :'psv_app'
          AND version = :psv_version - 1
          AND active
        \gset
    \elif :psv_do_reverse
      SELECT COUNT(*) = 0 AS psv_version_prec
        FROM PsvAppStatus
        WHERE app = :'psv_app'
          AND version = :psv_version + 1
          AND active
        \gset
      -- else dead code
    \endif

    \if :psv_debug
      \echo # DEBUG :psv_app :psv_operation :psv_version prec: :psv_version_prec
    \endif

    \if :psv_version_prec
      \if :psv_do_apply_catchup
        -- this app schema upgrade not already applied
        SELECT COUNT(*) = 0 AS psv_version_not_done
          FROM PsvAppStatus
          WHERE app = :'psv_app'
            AND version = :psv_version
            AND active
          \gset

        \if :psv_version_not_done
          -- we may have to do it
          \set psv_do_sigcheck 0
        \else
          \set psv_do_sigcheck 1
        \endif

      \elif :psv_do_reverse

        \set psv_do_sigcheck 0
        -- this downgrade can be executed
        SELECT COUNT(*) = 1 AS psv_version_not_done
          FROM PsvAppStatus
          WHERE app = :'psv_app'
            AND version = :psv_version
            AND active
          \gset
      -- else dead code
      \endif
    \else
      -- we have to skip this operation because the status is not right
      \set psv_version_not_done 0
      \set psv_do_sigcheck 0
    \endif
    \unset psv_version_prec

    \if :psv_debug
      \echo # DEBUG :psv_app :psv_operation :psv_version not done: :psv_version_not_done
    \endif

    -- and above/below target
    \if :psv_version_not_done

      -- filter out based on target version
      \if :psv_do_apply_catchup
        SELECT :psv_cmd_version = -1 OR :psv_version <= :psv_cmd_version AS psv_version_needed
        \gset
      \elif :psv_do_reverse
        SELECT :psv_cmd_version <> -1 AND :psv_version > :psv_cmd_version AS psv_version_needed
        \gset
      -- else dead code
      \endif
      -- override signature checks
      \set psv_do_sigcheck 0

    \else
      -- psv version was done
      \set psv_version_needed 0
    \endif
    \unset psv_version_not_done

    \if :psv_do_sigcheck

      -- check signature consistency in passing
      \if :psv_debug
        \echo # DEBUG checking signature consistency
      \endif

      -- app schema upgrade already applied with another script
      SELECT COUNT(*) = 0 AS psv_version_inconsistent
        FROM PsvAppStatus
        WHERE app = :'psv_app'
          AND version = :psv_version
          AND signature = :'psv_signature'
          AND active
        \gset

      -- this script was used somewhere already
      SELECT COUNT(*) > 0 AS psv_signature_used
        FROM PsvAppStatus
        WHERE app = :'psv_app'
          AND signature = :'psv_signature'
          AND active
        \gset

    \else
      -- no check, assume all is well
      \set psv_version_inconsistent 0
      \set psv_signature_used 0
    \endif
    \unset psv_do_sigcheck

    \if :psv_debug
      \echo # DEBUG :psv_app :psv_operate :psv_version for :psv_cmd_version_display: :psv_version_needed
    \endif

    \if :psv_version_needed
      -- app version to be executed
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
        INSERT INTO PsvAppStatus(app, version, signature, filename, description, command)
          VALUES (:'psv_app', :'psv_version', :'psv_signature', :'psv_filename', :'psv_description', :'psv_cmd');
      \else
        -- actual execution mode!
        \if :psv_signature_used
          -- will fail on UNIQUE(signature)
          \warn # ERROR :psv_app :psv_version script already applied
          \quit
        \endif

        \if :psv_dry
          \echo # psv will execute :psv_operate :psv_app :psv_version
            -- record the execution on the copy anyway
            \if :psv_do_apply
              INSERT INTO PsvAppStatus(app, version, signature, filename, description, command, active)
                VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description', :'psv_cmd', TRUE);
            \elif :psv_do_reverse
              BEGIN;
                UPDATE PsvAppStatus
                  SET active = FALSE
                  WHERE app = :'psv_app'
                    AND version = :'psv_version'
                    AND active;
                INSERT INTO PsvAppStatus(app, version, signature, filename, description, command, active)
                  VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description', :'psv_cmd', FALSE);
              COMMIT;
            -- else dead code
            \endif
        \else
          \echo # psv :psv_operating :psv_app :psv_version

    BEGIN;
"""

FILE_FOOTER = r"""
      \if :psv_do_apply_catchup
        -- upgrade application new version
        INSERT INTO PsvAppStatus(app, version, signature, filename, description, command)
          VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description', :'psv_cmd');
      \elif :psv_do_reverse
        UPDATE PsvAppStatus
          SET active = FALSE
          WHERE app = :'psv_app'
            AND version = :'psv_version'
            AND active;
        INSERT INTO PsvAppStatus(app, version, signature, filename, description, command, active)
          VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description', :'psv_cmd', FALSE);
      -- else dead code
      \endif

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
          BEGIN;
            UPDATE PsvAppStatus
              SET active = FALSE
              WHERE app = :'pvs_app'
                AND version = :'psv_version'
                AND active;
            INSERT INTO PsvAppStatus(app, version, signature, filename, description, command)
              VALUES (:'psv_app', :psv_version, :'psv_signature', :'psv_filename', :'psv_description', :'psv_cmd');
          COMMIT;
        \else
          \warn # ERROR :psv_app :psv_version inconsistent signature
          \quit
        \endif
      \endif
      \if :psv_dry
        \echo # psv will skip :psv_app :psv_operation :psv_version
      \else
        \echo # psv skipping :psv_app :psv_operation :psv_version
      \endif
    \endif
  \else
    -- step skipped as it does not apply to operation
    \if :psv_dry
      \echo # psv will ignore :psv_app :psv_operation :psv_version
    \else
      \echo # psv ignoring :psv_app :psv_operation :psv_version
    \endif
  \endif
 
  \unset psv_operation
  \unset psv_forward
  \unset psv_description
  \unset psv_signature
  \unset psv_version
  \unset psv_filename
"""

SCRIPT_FOOTER = APP_VERSION + r"""
\else
  -- do not apply steps
  \if :psv_dry
    \echo # psv will skip all steps for command :psv_cmd
  \else
    \echo # psv skipping all steps for command :psv_cmd
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
