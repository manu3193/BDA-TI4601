-- Semilla inmutable (solo corre en volumen vacío de Postgres).
-- Reset: docker compose down -v && docker compose up -d postgres

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

-- Cuenta para el laboratorio de concurrencia (S2 / U1).
CREATE TABLE accounts (
  id integer PRIMARY KEY,
  owner text NOT NULL,
  balance numeric NOT NULL CHECK (balance >= 0)
);

INSERT INTO accounts (id, owner, balance) VALUES (1, 'shared-row', 1000);
