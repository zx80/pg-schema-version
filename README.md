# _Simple_ Postgres Schema Versioning

There already exists _many_ tools to manage database schema versions, such as
[sqitch](https://sqitch.org/), [alembic](https://alembic.sqlalchemy.org/)
or [pgroll](https://github.com/xataio/pgroll).
Please consider them first to check whether they fit your needs before
considering this one.
In contrast to these tools, `pg-schema-version` emphasizes a _simple_ approach
based on a single plain `psql` SQL scripts and no configuration, to provide
limited but useful features with safety in mind.
The application schema status is maintained in one table to detect reruns,
including checking patch signatures.
Several application can share the same setup.

![Status](https://github.com/zx80/pg-schema-version/actions/workflows/test.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-11%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/pg-schema-version)
![License](https://img.shields.io/pypi/l/pg-schema-version?style=flat)
![Badges](https://img.shields.io/badge/badges-7-informational)

## Example Usage

Here is a typical use case for `pg-schema-version`:

1. Install from PyPi, e.g. with `pip`:

   ```shell
   pip install pg-schema-version
   ```

2. Write a sequence of incremental postgres SQL data definition scripts.
   The `-- psv:` comment header is mandatory to declare the application name,
   version and optional description.

   - initial schema creation `create_000.sql`

     ```sql
     -- psv: acme +1 Acme Schema v1.0
     CREATE TABLE AcmeData(aid SERIAL PRIMARY KEY, data TEXT UNIQUE NOT NULL);
     ```

   - first schema upgrade `create_001.sql`

     ```sql
     -- psv: acme +2 Acme Schema v1.1
     CREATE TABLE AcmeType(atid SERIAL PRIMARY KEY, atype TEXT UNIQUE NOT NULL);
     INSERT INTO AcmeType(atype) VALUES ('great'), ('super');
     ALTER TABLE AcmeData ADD COLUMN atid INT NOT NULL DEFAULT 1 REFERENCES AcmeType;
     ```

   - second schema upgrade `create_002.sql`

     ```sql
     -- psv: acme +3 Acme Schema v2.0
     INSERT INTO AcmeType(atype) VALUES ('wow'), ('incredible');
     ```

3. Generate a `psql`-script from these for the target application:

   ```shell
   pg-schema-version create_*.sql > acme.sql
   ```

4. Execute the script against a database to bring its schema up to date.
   By default the script runs in _dry_ mode and reports the proposed changes to
   be applied by setting it in _wet_ mode.

   ```shell
   # first time can use command create to init the setup and register the app.
   psql -v psv=create acme < acme.sql
   # psv for application acme
   # psv dry create for acme on acme, enable with -v psv=create:latest:wet
   # psv will create infra, register acme and execute all steps

   psql -v psv=create:wet acme < acme.sql
   # psv for application acme
   # psv wet create for acme on acme
   # psv creating infra
   # psv registering acme
   # psv considering applying steps
   # psv acme version: 0
   # psv applying acme 1
   # psv applying acme 2
   # psv applying acme 3
   # psv acme version: 3
   # psv wet create for acme done

   # on rerun, do nothing
   psql -v psv=wet acme < acme.sql
   # psv for application acme
   # psv wet apply for acme on acme
   # psv skipping acme registration
   # psv considering applying steps
   # psv acme version: 3
   # psv skipping acme 1
   # psv skipping acme 2
   # psv skipping acme 3
   # psv acme version: 3
   # psv wet apply for acme done

   # show current status
   psql -v psv=status acme < acme.sql
   # …
   ```

   > | app  | version | description      |
   > |---   |     ---:|---               |
   > | acme |       3 | Acme Schema v2.0 |
   > | psv  |       0 | •                |

## Features

See `pg-schema-version --help` for a synopsis and explanations of all available
options.

The python command generates a reasonably safe re-entrant idempotent `psql`
script driven by variable `psv` with value _command_:_version_:_moist_

- available commands are (default is `apply`):
  - `init` just initialize an empty psv infrastructure.
  - `register` add new application to psv versioning.
  - `apply` execute required steps on an already registered application.
  - `reverse` execute scripts to reverse steps.
  - `create` do the 3 phases above: init, register and apply.
  - `unregister` remove application from psv versioning.
  - `remove` drop psv infrastructure.
  - `help` show some help.
  - `status` show version status of applications.
  - `history` show history of application changes.
  - `catchup` update application version status without actually executing steps
    (imply init and register).
- versions are integers designating the target step, default is `latest`.
- available moistures are (default is `dry`):
  - `dry` meaning that no changes are applied.
  - `wet` to trigger actual changes.

Each provided script **must** contain a special `-- psv: name +5432 description`
header with:

- `name` the application name, which **must** be consistent accross all scripts.
- `+5432` the version for apply (`+`) or reverse (`-`) a schema step, which
  will be checked for inconsistencies such as repeated or missing versions.
- `description` an optional description of the resulting application status,
  eg the corresponding application version.

Beware that reversing may help you lose precious data, and that it is your
responsability that the provided reverse scripts undo what was done by the
forward scripts.

Other options at the `psql` script level:

- `-v psv_debug=1` to set debug mode.
- `-v psv_app=foo` to change the application registration name.
  Probably a bad idea.

## Caveats

Always:

- have a working (i.e. actually tested) backup of your data.
- run _dry_  and read the output carefully before running _wet_.
- test your scripts with care before applying it to production data.

There is no magic involved, you can still shot yourself in the foot, although
with an effort.
For safety, SQL schema creation scripts must **not**:

- include backslash commands which may interfere with the script owns.
- include SQL transaction commands.

Imperfect checks are performed to try to detect the above issues.
They can be circumvented with option `--trust-scripts` or `-T`.

## Versions

### TODO

- default phase? status? run? help?
- check? `foo =n …`? so what?
- on partial, detect missing path before trying?
  at least report of target is not reached!
- add synopsis and document all options
- write a tutorial
- write recipes
- test setting `psv_app`

### 1.0 on 2025-04-08

- split and count actual test scenarii
- use SPDX licensing format
- improve CI
- switch to stable, as it is already used and working for an internal project

### 0.6 on 2024-10-27

- be stricter about backslash command detection
- improve documentation

### 0.5 on 2024-10-22

- add `reverse` command to allow going backwards, and tests
- add `history` command to show application history of changes
- keep step execution history
- differentiate exit status depending on the error
- add `--version` option
- check app and hash option values
- keep executed commands and session users
- add debug mode
- fix `psv` command parsing
- add reverse catchup tests

### 0.4 on 2024-10-20

- make psv comment header (`-- psv: foo +1 …`) mandatory,
  including many sanity checks about names, versions…
- rename `run` to `apply`
- show status only when asked
- add `--partial` option to allow partial scripts (i.e. missing versions)
- use `--app` to check script consistency
- check current status strictly before applying a step
- improve documentation, esp. the example
- improve tests about descriptions
- refactor script sources

### 0.3 on 2024-10-19

- add unregister and catchup commands
- add setting a version target for a run
- add filename and description fields
- add verbose option
- show description on status
- escape schema and table identifiers
- refactor application registration
- improve documentation

### 0.2 on 2024-10-15

- activate GitHub pages
- working GitHub CI
- add coverage check
- add markdown check
- use exit code 3 for output file

### 0.1 on 2024-10-14

- initial beta version for testing

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

See [online documentation](https://zx80.github.io/pg-schema-version/).
Sources and issues are on [GitHub](https://github.com/zx80/pg-schema-version).
Packages are distributed from [PyPi](https://pypi.org/project/pg-schema-version/).

All software has bug, this is software, hence…
Beware that you may lose your hairs or your friends because of it.
If you like it, feel free to send a postcard to the author.
