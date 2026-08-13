# Instituto Tecnológico de Costa Rica

## TI-4601 Bases de Datos Avanzados — entorno de estudiantes

Orquestación con Docker Compose.

Copyright: Instituto Tecnológico de Costa Rica.

---

## Guía de ejecución

```bash
git clone <url> ti4601 && cd ti4601
make up          # postgres + volumen + seed en initdb
make verify      # smoke test pipeline ACID
```

Éxito: saldo/filas de John y Jane en `answer`, mensaje «Entorno listo».

```bash
make test-tx
make lab-concurrency ISOLATION=READ_COMMITTED
make lab-concurrency ISOLATION=SERIALIZABLE
make shell       # PGHOST=postgres inyectado por Compose
```



## Credenciales (inyectadas; no hardcodear en código)


| Variable     | Postgres (`app`) | Cockroach (`app-crdb`) |
| ------------ | ---------------- | ---------------------- |
| `PGHOST`     | `postgres`       | `crdb-1`               |
| `PGPORT`     | `5432`           | `26257`                |
| `PGUSER`     | `ti4601`         | `root`                 |
| `PGPASSWORD` |                  |                        |
| `PGDATABASE` | `ti4601`         | `ti4601`               |


Desde el host (opcional): `psql` a `127.0.0.1:5433`. 

## Persistencia

Datos Postgres viven en el volumen `pgdata`.  Para eliminar volúmenes use: `make down -v` .

Para volver a levantar use `make up` (vuelve a correr `/docker-entrypoint-initdb.d`).

## Archivos principales


| Ruta                   | Rol                                       |
| ---------------------- | ----------------------------------------- |
| `docker-compose.yml`   | Red `ti4601`, postgres, app, clúster lab1 |
| `db/init/`             | Schema + CSV → `initdb`                   |
| `transactions/`        | Pipeline ACID                             |
| `labs/01-concurrency/` | Estrés de aislamiento                     |
| `Makefile`             | Única interfaz operativa                  |




## Fallos comunes


| Síntoma                    | Qué hacer                                               |
| -------------------------- | ------------------------------------------------------- |
| init no carga CSV          | Volumen viejo: `make down-v && make up`                 |
| `connection refused`       | `make up` y esperar healthcheck                         |
| Puerto 5433 ocupado        | cambiar puerto en .env                                  |
| `psycopg` en el host       | Use `make shell` / `compose run`; no el Python del host |
| CRDB “already initialized” | Normal tras el primer `lab1-up`                         |


