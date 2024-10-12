# Lightweight Postgres Schema Versioning

There already exists tools to manage database schema versions, such as
[sqitch](https://sqitch.org/), or [alembic](https://alembic.sqlalchemy.org/).
In contrast, pg-schema-version (`psv`) emphasizes a _simple_ approach based on
plain SQL scripts and no configuration to provide limited but useful features
with safety first in mind.

## Usage

1. Write a sequence of incremental postgres SQL data definition scripts

   - initial schema creation `create_000.sql`
     ```sql
     CREATE TABLE AcmeData(aid SERIAL PRIMARY KEY, data TEXT UNIQUE NOT NULL);
     ```
   - first schema upgrade `create_001.sql`
     ```sql
     CREATE TABLE AcmeType(atid SERIAL PRIMARY KEY, atype TEXT UNIQUE NOT NULL);
     INSERT INTO AcmeType(atype) VALUES ('great'), ('super'), ('wow');
     ALTER TABLE AcmeData ADD COLUMN atid INT NOT NULL DEFAULT 1 REFERENCES AcmeType;
     ```

2. Generate a `psql`-script from these:
   ```shell
   psv create_*.sql > acme.sql
   ```

3. Execute the script against a database to bring its schema up to date.
   ```shell
   psql acme < acme.sql
   # psv dry run for app acme, enable with -v psv_wet_run=1
   # script will create infratructure and execute all commands

   psql -v psv_wet_run=1 < acme.sql
   # psv wet run for app acme
   # creating psv infrastructure
   # creating acme version 1
   # creating acme version 2
   # acme version: 2
   ```

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence…
Beware that you may lose your hairs or your friends because of it.
If you like it, feel free to send a postcard to the author.
