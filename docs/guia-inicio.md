# Guía de inicio — Semana 2

Filosofía (`bigdataclass/`): **un script = una acción**, sin Compose “de producción”.

## Requisitos

Docker Engine, Python 3, Git. ~700 MB para `postgres:16`.

## Pasos

```bash
chmod +x scripts/*.sh transactions/*.sh
make verify
```

Qué comprueba:

1. `docker`, `python3`, `curl`, `git`
2. Contenedor `ti4601-postgres` responde (`pg_isready`)
3. Python puede usar `csv` (stdlib)

## Fallos comunes

| Síntoma | Qué hacer |
| --- | --- |
| `docker` FAIL | Arrancar Docker |
| Puerto ocupado | `POSTGRES_PORT=5434 ./scripts/up.sh` |
| Postgres lento al primer pull | Esperar; `docker pull postgres:16` antes de clase |

## Ejemplo transactions

```bash
cd transactions
./read.sh
./transform.sh
./aggregate.sh
./join.sh
./answer.sh
```

Python puro — **no** Spark.

## SQL opcional

```bash
./scripts/load_db.sh
docker exec -it ti4601-postgres psql -U ti4601 -d ti4601
```
