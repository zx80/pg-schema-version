# Lightweight Postgres Schema Versioning

There already exists _many_ tools to manage database schema versions, such as
[sqitch](https://sqitch.org/), or [alembic](https://alembic.sqlalchemy.org/).
Please consider them first to check whether they fit your needs before
considering this one.
In contrast to these tools, `pg-schema-version` emphasizes a _simple_ approach
based on a single plain SQL scripts and no configuration, to provide limited but
useful features with safety in mind.
The application schema status is maintained in one table to detect reruns.
Several application can share the same setup.

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
   psql -v psv_cmd=create acme < acme.sql
   # psv command set to create
   # psv dry create for acme, enable with -v psv_wet=1
   # psv script will create infra, register acme and execute all steps

   psql -v psv_cmd=create -v psv_wet=1 < acme.sql
   # psv wet run for acme
   # psv creating psv infra
   # psv registering app acme
   # psv applying acme 1
   # psv applying acme 2
   # psv applying acme 3
   # psv acme version: 3
   # psv wet run for acme done

   # on rerun, do nothing
   psql -v psv_wet=1 < acme.sql
   # psv wet run for app acme
   # psv applying acme 1
   # psv applying acme 2
   # psv applying acme 3
   # psv acme version: 3
   # psv wet run for acme done
   ```

## Features

The python script generates a reasonably safe re-entrant idempotent SQL script
driven by `psql`-variables `psv_cmd` and `psv_wet`:

- if `psv_wet` is not set, the script only performs a dry run which does **not**
  apply any schema changes.
- available `psv_cmd` commands are:
  - `init` just initialize an empty psv infrastructure if needed.
  - `register` register new application in the psv infrastructure if needed.
  - `run` run required steps on an already registered application.
  - `create` do all of the above.
  - `remove` drop psv infrastructure.

## Caveats

There is no magic involved, you can still shot yourself in the foot, although
with an effort.

To be safe, SQL schema creation scripts must **NOT**:
- include backslash commands which may interfere with the script owns.
- include SQL transaction commands.

Imperfect checks are performed to detect the above issues.
They can be circumvented with option `--trust-scripts`.

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence…
Beware that you may lose your hairs or your friends because of it.
If you like it, feel free to send a postcard to the author.
