-- psv: acme +2 Acme application first upgrade with types.

CREATE TABLE AcmeType(
  atid SERIAL PRIMARY KEY,
  atype TEXT UNIQUE NOT NULL
);

INSERT INTO AcmeType(atype) VALUES
  ('great'),
  ('super')
;

ALTER TABLE AcmeData
  ADD COLUMN atid INT NOT NULL DEFAULT 1 REFERENCES AcmeType;
