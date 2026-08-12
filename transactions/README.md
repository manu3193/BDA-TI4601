# Ejemplo `transactions` — Semana 2

Misma progresión que `bigdataclass/transactions/`, pero:

- **Python + SQL** contra la imagen oficial **Postgres** (`scripts/up.sh`)
- **No** Spark

Los CSV solo sirven para **cargar** la BD (`scripts/load_db.sh`).

## Preparar

```bash
../scripts/up.sh
../scripts/load_db.sh
# o prueba completa:
../scripts/test_transactions.sh
```

Variables (defaults):

| Variable | Default |
| --- | --- |
| `PGHOST` | `localhost` (desde host) o `host.docker.internal` (desde `run_image.sh`) |
| `PGPORT` | `5433` |
| `PGUSER` / `PGPASSWORD` / `PGDATABASE` | `ti4601` |

## Pasos

```bash
cd transactions
./read.sh         # SELECT desde transactions
./transform.sh    # fechas tipadas en SQL
./aggregate.sh    # GROUP BY cliente/día
./join.sh         # JOIN customers
./answer.sh       # JOIN exchange_rates → adjusted_amount
```

Dentro de la imagen de trabajo:

```bash
./build_image.sh && ./run_image.sh
# ya con PGHOST=host.docker.internal
cd transactions && ./answer.sh
```
