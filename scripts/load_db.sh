#!/usr/bin/env bash
# Carga esquema + CSVs de transactions/ en Postgres (imagen oficial).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME=ti4601-postgres
TX="${ROOT}/transactions"

"${ROOT}/scripts/up.sh"
for _ in $(seq 1 30); do
  if docker exec "${NAME}" pg_isready -U ti4601 >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec -i "${NAME}" psql -U ti4601 -d ti4601 < "${ROOT}/db/initialize.sql"

docker exec -i "${NAME}" psql -U ti4601 -d ti4601 -c \
  "COPY transactions (customer_id, amount, purchased_at) FROM STDIN WITH (FORMAT csv, HEADER true)" \
  < "${TX}/transactions.csv"

docker exec -i "${NAME}" psql -U ti4601 -d ti4601 -c \
  "COPY customers (id, name, currency) FROM STDIN WITH (FORMAT csv, HEADER true)" \
  < "${TX}/names.csv"

docker exec -i "${NAME}" psql -U ti4601 -d ti4601 -c \
  "COPY exchange_rates (currency, rate) FROM STDIN WITH (FORMAT csv, HEADER true)" \
  < "${TX}/exchange_rates.csv"

echo "Postgres cargado: transactions + customers + exchange_rates"
docker exec "${NAME}" psql -U ti4601 -d ti4601 -c \
  "SELECT 'transactions' AS t, count(*) FROM transactions
   UNION ALL SELECT 'customers', count(*) FROM customers
   UNION ALL SELECT 'exchange_rates', count(*) FROM exchange_rates;"
