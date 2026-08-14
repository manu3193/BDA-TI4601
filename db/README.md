# db/

Semilla **inmutable** de Postgres via `docker-entrypoint-initdb.d`
(montado desde `db/init/` en `docker-compose.yml`).

| Archivo | Rol |
| --- | --- |
| `init/01_schema.sql` | Tablas transactions + accounts (lab concurrencia) |
| `init/02_load.sql` | `COPY` desde `init/data/*.csv` |
| `init/data/` | CSV canónicos del seed |

Solo corre cuando el volumen `pgdata` está vacío → `make down-v && make up` para
re-sembrar.
