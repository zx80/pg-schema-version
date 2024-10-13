# Lightweight Postgres Schema Versioning

There already exists tools to manage database schema versions, such as
[sqitch](https://sqitch.org/), or [alembic](https://alembic.sqlalchemy.org/).
Please consider them to check whether they fit your needs before considering psv.
In contrast, pg-schema-version (`psv`) emphasizes a _simple_ approach based on
a single plain SQL scripts and no configuration to provide limited but useful
features with safety first in mind.

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

2. Generate a `psql`-script from these:
   ```shell
   pg-schema-version -a acme create_*.sql > acme.sql
   ```

3. Execute the script against a database to bring its schema up to date.
   ```shell
   # first time MUST use create
   psql -v psv_cmd=create acme < acme.sql
   # psv command set to run, set with -v psv_cmd=…
   # psv dry run for acme, enable with -v psv_wet_run=1
   # script will create infra, register acme and execute all steps

   psql -v psv_cmd=create -v psv_wet_run=1 < acme.sql
   # psv wet run for acme
   # creating psv infrastructure
   # registering app acme
   # applying acme 1
   # applying acme 2
   # applying acme 3
   # acme version: 3

   # on rerun, do nothing
   psql -v psv_wet_run=1 < acme.sql
   # psv wet run for app acme
   # skipping psv infrastructure
   # applying acme 1
   # applying acme 2
   # applying acme 3
   # acme version: 3
   ```

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence…
Beware that you may lose your hairs or your friends because of it.
If you like it, feel free to send a postcard to the author.
