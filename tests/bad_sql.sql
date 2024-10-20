-- psv: bad +2 transactions are not welcome
SELECT 'hello world!'; 
 BEGIN;
    SELECT 1 AS one;
  COMMIT;
