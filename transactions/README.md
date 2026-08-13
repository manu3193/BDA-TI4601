# transactions/ — pipeline ACID

Cada paso abre conexión con `dbutil.connect()`, usa
`with conn.transaction():` y empuja el trabajo al motor con `CREATE TEMP TABLE`
cuando hay transformación/agregación/join.

```bash
make test-tx
# equivalente:
# docker compose run --rm app python3 transactions/answer.py
```

Variables `PG*` las inyecta Compose. No ponga IPs en el código.

Semilla CSV: `db/init/data/` (copia de los CSV de esta carpeta para `initdb`).
