# Ejemplo `transactions`

Misma progresión que `bigdataclass/transactions/`, pero:

- **Python + SQL** contra Postgres (`scripts/up.sh`)
- **No** Spark
- Ejecución **vía Docker** (`make test-tx` o `./run_image.sh`)

Los CSV solo cargan la BD (`scripts/load_db.sh`).

## Camino recomendado

Desde la raíz del repo:

```bash
./scripts/up.sh
./scripts/load_db.sh
make test-tx
```

O:

```bash
./scripts/up.sh && ./scripts/load_db.sh
./run_image.sh
# dentro:
cd transactions
./read.sh && ./transform.sh && ./aggregate.sh && ./join.sh && ./answer.sh
```

## No recomendado: Python del host

`./read.sh` en el host falla sin `psycopg` y sin la red Docker. No es el camino de clase.

## Variables (dentro de Docker)

| Variable | Valor |
| --- | --- |
| `PGHOST` | `ti4601-postgres` |
| `PGPORT` | `5432` |
| `PGUSER` / `PGPASSWORD` / `PGDATABASE` | `ti4601` |

## Pasos del pipeline

| Script | Qué hace |
| --- | --- |
| `read.sh` | `SELECT` de `transactions` |
| `transform.sh` | Fechas tipadas en SQL |
| `aggregate.sh` | `GROUP BY` cliente/día |
| `join.sh` | `JOIN customers` |
| `answer.sh` | `JOIN exchange_rates` → `adjusted_amount` |
