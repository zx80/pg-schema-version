# Lightweight Postgres Schema Versioning

There already exists tools to manage database schema versions, such as
[sqitch](https://sqitch.org/), or [alembic](https://alembic.sqlalchemy.org/).
In contrast, pg-schema-version (`psv`) emphasizes a _simple_ approach based on
plain SQL scripts and no configuration to provide limited but useful features.

## Usage

1. Write a sequence of incremental postgres SQL data definition scripts

   - initial creation `create_000.sql`
     ```sql
     CREATE TABLE Acme(aid SERIAL PRIMARY KEY, data TEXT UNIQUE NOT NULL);
     ```
   - first update `create_001.sql`
     ```sql
     CREATE TABLE AcmeType(atid SERIAL PRIMARY KEY, atype TEXT UNIQUE NOT NULL);
     ALTER TABLE Acme ADD COLUMN atid INT8 NOT NULL REFERENCES AcmeType;
     ```

2. Generate a `psql`-script from these:
   ```shell
   psv create_*.sql > out.sql
   ```

3. Execute the script against a database to bring its schema up to date.
   ```shell
   psql acme < out.sql
   ```

## License

This code is [Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

All software has bug, this is software, hence…
Beware that you may lose your hairs or your friends because of it.
If you like it, feel free to send a postcard to the author.
