-- Esquema del ejemplo transactions (Semana 2).
BEGIN;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS exchange_rates;

CREATE TABLE transactions (
  customer_id integer NOT NULL,
  amount numeric NOT NULL,
  purchased_at timestamp without time zone NOT NULL
);

CREATE TABLE customers (
  id integer PRIMARY KEY,
  name text NOT NULL,
  currency text NOT NULL
);

CREATE TABLE exchange_rates (
  currency text PRIMARY KEY,
  rate numeric NOT NULL
);

COMMIT;
