# _Simple_ Postgres Schema Versioning

There already exists _many_ tools to manage database schema versions, such as
[sqitch](https://sqitch.org/), or [alembic](https://alembic.sqlalchemy.org/).
Please consider them first to check whether they fit your needs before
considering this one.
In contrast to these tools, `pg-schema-version` emphasizes a _simple_ approach
based on a single plain SQL scripts and no configuration, to provide limited but
useful features with safety in mind.
The application schema status is maintained in one table to detect reruns.
Several application can share the same setup.

![Status](https://github.com/zx80/pg-schema-version/actions/workflows/test.yml/badge.svg?branch=main&style=flat)
![Tests](https://img.shields.io/badge/tests-217%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/pg-schema-version)
![License](https://img.shields.io/pypi/l/pg-schema-version?style=flat)
![Badges](https://img.shields.io/badge/badges-7-informational)

## Usage

1. Install from PyPi, e.g. with `pip`:

   ```shell
   pip install pg-schema-version
   ```

2. Write a sequence of incremental postgres SQL data definition scripts

   - initial schema creation `create_000.sql`

     ```sql
     CREATE TABLE AcmeData(aid SERIAL PRIMARY KEY, data TEXT UNIQUE NOT NULL);
     ```

   - first schema upgrade `create_001.sql`

     ```sql
     CREATE TABLE AcmeType(atid SERIAL PRIMARY KEY, atype TEXT UNIQUE NOT NULL);
     INSERT INTO AcmeType(atype) VALUES ('great'), ('super');
     ALTER TABLE AcmeData ADD COLUMN atid INT NOT NULL DEFAULT 1 REFERENCES AcmeType;
     ```

   - second schema upgrade `create_002.sql`

     ```sql
     INSERT INTO AcmeType(atype) VALUES ('wow'), ('incredible');
     ```

3. Generate a `psql`-script from these for the target application:

   ```shell
   pg-schema-version -a acme create_*.sql > acme.sql
   ```

4. Execute the script against a database to bring its schema up to date.

   ```shell
   # first time MUST use command create
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
   ┌──────┬─────────┬──────────────────────────────────┐
   │ app  │ version │           description            │
   ├──────┼─────────┼──────────────────────────────────┤
   │ acme │       3 │ Acme application with more types │
   │ psv  │       0 │ •                                │
   └──────┴─────────┴──────────────────────────────────┘
   ```

## Features

The python script generates a reasonably safe re-entrant idempotent SQL script
driven by `psql`-variable `psv` with value _command_:_version_:_moist_

- available commands are (default is `apply`):
  - `init` just initialize an empty psv infrastructure.
  - `register` add new application to psv versioning.
  - `apply` execute required steps on an already registered application.
  - `create` do the 3 phases above: init, register and apply.
  - `unregister` remove application from psv versioning.
  - `remove` drop psv infrastructure.
  - `help` show some help.
  - `status` show version status of applications.
  - `catchup` update application version status without actually executing steps
    (imply init and register).
- versions are integers designating the target step, default is `latest`.
- available moistures are (default is `dry`):
  - `dry` meaning that no changes are applied.
  - `wet` to trigger actual changes.

The only way is forward: there is no provision to go back to a previous
state. However, note that schema steps are performed in a transaction, so
that it can only fail one full step at a time.

If a script contains a special `-- psv: some description` comment, the
description is recorded and shown on command `status`.

## Caveats

Only dream of running the generated SQL scripts if you have a working (i.e.
actually tested) backup of your data.

Always run _dry_  and read the output carefully before running _wet_.

There is no magic involved, you can still shot yourself in the foot, although
with an effort.

For safety, SQL schema creation scripts must **NOT**:

- include backslash commands which may interfere with the script owns.
- include SQL transaction commands.

Imperfect checks are performed to try to detect the above issues.
They can be circumvented with option `--trust-scripts`.

Always test your scripts with care before applying it to production data.

## Versions

### TODO

- check provided strings, eg app name and others? escaping?
- default phase? status? run? help?
- reverse? check?
  - each file contains a mandatory declaration `-- psv: …`
  - `foo +n` `foo =n` `foo -n` : app foo schema n, check n, reverse n.
  - option `-K --keep` to keep file order
  - `-a foo` is used to check the application name
  - must check that a continuous path exists before applying anything!
- write a tutorial
- write recipes

### ? on ?

- rename `run` to `apply`
- show status when asked
- improve documentation, esp. the example
- improve tests about descriptions

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
