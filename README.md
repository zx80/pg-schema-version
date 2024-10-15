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
![Tests](https://img.shields.io/badge/tests-156%20✓-success)
![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Python](https://img.shields.io/badge/python-3-informational)
![Version](https://img.shields.io/pypi/v/pg-schema-version)
![License](https://img.shields.io/pypi/l/pg-schema-version?style=flat)
![Badges](https://img.shields.io/badge/badges-7-informational)

## Usage

1. Write a sequence of incremental postgres SQL data definition scripts

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

2. Generate a `psql`-script from these for the target application:

   ```shell
   pg-schema-version -a acme create_*.sql > acme.sql
   ```

3. Execute the script against a database to bring its schema up to date.

   ```shell
   # first time MUST use command create
   psql -v psv=create acme < acme.sql
   # psv command set to create
   # psv dry create for acme, enable with -v psv=create:wet
   # psv script will create infra, register acme and execute all steps

   psql -v psv=create:wet < acme.sql
   # psv wet run for acme
   # psv creating psv infra
   # psv registering app acme
   # psv applying acme 1
   # psv applying acme 2
   # psv applying acme 3
   # psv acme version: 3
   # psv wet run for acme done

   # on rerun, do nothing
   psql -v psv=wet < acme.sql
   # psv wet run for app acme
   # psv skipping acme 1
   # psv skipping acme 2
   # psv skipping acme 3
   # psv acme version: 3
   # psv wet run for acme done
   ```

## Features

The python script generates a reasonably safe re-entrant idempotent SQL script
driven by `psql`-variable `psv` with value _command_:_moist_

- available commands are (default is `run`):
  - `init` just initialize an empty psv infrastructure if needed.
  - `register` add new application to psv versioning if needed.
  - `run` apply required steps on an already registered application.
  - `create` do all of the above.
  - `unregister` remove application from psv versioning if needed.
  - `remove` drop psv infrastructure.
  - `help` show some help.
  - `status` show version status of applications.
- available moistures are (default is `dry`):
  - `dry` meaning that no changes are applied.
  - `wet` to trigger actual changes.

The only way is forward: there is no provision to go back to a previous
state. However, note that schema steps are performed in a transaction, so
that it can only fail one full step at a time.

## Caveats

There is no magic involved, you can still shot yourself in the foot, although
with an effort.

To be safe, SQL schema creation scripts must **NOT**:
- include backslash commands which may interfere with the script owns.
- include SQL transaction commands.

Imperfect checks are performed to detect the above issues.
They can be circumvented with option `--trust-scripts`.

Test your scripts with care before applying it to production data.

## Versions

### TODO

- reorder register conditions
- catchup?
- reverse?
- version?
- verbose mode?
- add description?

### ? on ?

- add unregister command.

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

All software has bug, this is software, hence…
Beware that you may lose your hairs or your friends because of it.
If you like it, feel free to send a postcard to the author.
