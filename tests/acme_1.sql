-- psv: Acme application initial schema

CREATE TABLE AcmeData(
  aid SERIAL PRIMARY KEY,
  data TEXT UNIQUE NOT NULL
);
