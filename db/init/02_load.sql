-- Carga CSV montados en /docker-entrypoint-initdb.d/data/
COPY transactions (customer_id, amount, purchased_at)
  FROM '/docker-entrypoint-initdb.d/data/transactions.csv'
  WITH (FORMAT csv, HEADER true);

COPY customers (id, name, currency)
  FROM '/docker-entrypoint-initdb.d/data/names.csv'
  WITH (FORMAT csv, HEADER true);

COPY exchange_rates (currency, rate)
  FROM '/docker-entrypoint-initdb.d/data/exchange_rates.csv'
  WITH (FORMAT csv, HEADER true);
