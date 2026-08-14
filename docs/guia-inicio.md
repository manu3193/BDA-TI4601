# Guía corta — entorno + labs

## Semana 2 (hoy: smoke, no Lab 0)

1. `make up` + `make build`.  
2. Verificar a mano (README raíz):

```bash
docker compose exec -T postgres pg_isready -U ti4601 -d ti4601
docker compose run --rm app python3 transactions/answer.py
```

3. Teoría de aislamiento en clase (prerreq Lab 0).  
4. Lab 0 se ejecuta en **S3**: `labs/lab0-concurrency/README.md`.

## Después

| Semana | Qué |
| --- | --- |
| S3 | Lab 0 + kickoff P1 |
| S4 | Shard key P1 + prep métricas Lab 2 |
| S5 | Lab 1: `labs/lab1-cluster/` |
| S7 | Lab 2: `labs/lab2-queries/` |

Índice: `labs/README.md` · Makefile: `labs/lab1-cluster/README-makefile.md`.

Reset Postgres: `make down-v && make up`.
