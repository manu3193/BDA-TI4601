# Ejemplo `transactions` — Semana 2

Misma progresión que `bigdataclass/transactions/`, pero en **Python puro**
(stdlib `csv` / `datetime`). **No** usa Spark: TI-4601 no porta el stack JVM
([F: propuesta-integracion-bigdata.md]).

## Pasos (un script = una acción)

```bash
cd transactions
chmod +x *.sh
./read.sh         # leer CSV
./transform.sh    # tipar / formatear fechas
./aggregate.sh    # sumar amount por cliente y día
./join.sh         # unir names.csv
./answer.sh       # aplicar exchange_rates.csv
```

Datos: `transactions.csv`, `names.csv`, `exchange_rates.csv` (mismos del curso Big Data).

## Opcional — cargar a Postgres

```bash
../scripts/up.sh
../scripts/load_db.sh
docker exec -it ti4601-postgres psql -U ti4601 -d ti4601 -c 'SELECT * FROM transactions;'
```

Puerto por defecto del contenedor: **5433** (como el Postgres auxiliar de Big Data).
