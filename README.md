# Instituto Tecnológico de Costa Rica
## TI-4601 Bases de Datos Avanzados — entorno de estudiantes

Orquestación con Docker Compose. No instale `psycopg` en su computadora, todo debe ser ejecutado desde la imagen de docker del curso, ahí deben ejecutar sus programas, **dentro** del contenedor `app` (o `app-crdb` en Lab 1).

Copyright: Instituto Tecnológico de Costa Rica.

---

## Arranque

```bash
git clone <url> ti4601 && cd ti4601
make up
make build
```

Luego verifique el entorno **a mano** siguiendo estos pasos:

### Verificación del entorno 


```bash
# 1) Levantar motor
make up

# 2) Compilar imagen de docker del curso
make build

# 3) Comprobar que postgres acepta conexiones
docker compose exec -T postgres pg_isready -U ti4601 -d ti4601

# 4) Smoke test del pipeline (ejemplo canónico de Python en Docker con transacciones)
docker compose run --rm app python3 transactions/answer.py
```

Éxito en el paso 4: filas de **John** y **Jane** con `adjusted_amount` (p. ej. 108000.0,
57600.0, 76800.0, 900.0, 49.5).

Equivalente genérico para **cualquier** script del repo:

```bash
make up
docker compose run --rm app python3 ruta/al/script.py
# interactivo:
make shell
python3 ruta/al/script.py
```

Compose inyecta `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`. El código
usa libpq (`psycopg.connect()` sin hardcodear IPs).

| Objetivo | Comando |
| --- | --- |
| Smoke test | pasos de verificación el entorno |
| Pipeline completo | `make test-tx` |
| Un solo paso | `docker compose run --rm app python3 transactions/read.py` |
| Shell con PG* | `make shell` |
| Lab 0 concurrencia | `make lab-concurrency` · `labs/lab0-concurrency/` |
| Lab 1 clúster (S5+) | `labs/lab1-cluster/` |
| Lab 2 one size (S9) | `make lab2-up` · `labs/lab2-one-size/` |
| Lab 3 réplicas MongoDB (S10) | `make lab3-up` · `labs/lab3-mongo-replicas/` |
| Lab 4 actas en Neo4j (S13) | `make lab4-up` · `labs/lab4-neo4j/` |

Índice: [`labs/README.md`](labs/README.md).

---

## Labs

| # | Carpeta | Semana |
| --- | --- | --- |
| 0 | [`lab0-concurrency/`](labs/lab0-concurrency/) | S3 · Postgres · lost update (teoría S2) · **2,5 %** |
| 1 | [`lab1-cluster/`](labs/lab1-cluster/) | S5 · Cockroach · quórum / P1 · **2,5 %** |
| 2 | [`lab2-one-size/`](labs/lab2-one-size/) | S9 · Postgres + Valkey · one size fits all · **2,5 %** |
| 3 | [`lab3-mongo-replicas/`](labs/lab3-mongo-replicas/) | S10 · MongoDB · réplicas, mayoría, elección · **2,5 %** (+ Tarea 3, 1,5 %) |
| 4 | [`lab4-neo4j/`](labs/lab4-neo4j/) | S13 · Neo4j · actas municipales · **2,5 %** |
| 5 | se publica S15 | S15 · vectores + integración · **2,5 %** |

```bash
make lab-concurrency ISOLATION=READ_COMMITTED
make lab-concurrency ISOLATION=SERIALIZABLE
```

---

## Credenciales (inyectadas; no hardcodear)

| Variable | Postgres (`app`) | Cockroach (`app-crdb`) |
| --- | --- | --- |
| `PGHOST` | `postgres` | `crdb-1,crdb-2,crdb-3` |
| `PGPORT` | `5432` | `26257` |
| `PGUSER` | `ti4601` | `root` |
| `PGPASSWORD` | `ti4601` | *(vacío, inseguro)* |
| `PGDATABASE` | `ti4601` | `ti4601` |
| `PGSSLMODE` | — | `disable` |

Lab 3 (`app-mongo`) usa `MONGO_URI=mongodb://mongo-1:27017,mongo-2:27017,mongo-3:27017/?replicaSet=rs-lab3`
y `MONGO_DB=boleteria`. Los miembros de MongoDB no publican puertos al host.

Lab 4 publica Neo4j en `127.0.0.1:7474` y `127.0.0.1:7687` (`neo4j` / `ti4601-grafos`) y el notebook en `http://127.0.0.1:8888/lab?token=ti4601`. El modelo preentrenado va dentro de la imagen; no hay clave de API.

Host opcional: `psql` → `127.0.0.1:5433`. UI de CRDB → `http://127.0.0.1:8080`.

Lab 1 usa multi-region SQL (`REGIONAL BY ROW` / `GLOBAL`). Un clúster nuevo `v24.3.0`
tiene siete días de gracia; para conservarlo durante todo el P1 copie `.env.example` a
`.env` en la raíz y use allí el valor `COCKROACH_LICENSE` provisto por el docente.
El archivo está ignorado por git.

## Persistencia

Datos en el volumen `pgdata`. `make down` no los borra.  
Para reiniciar por completo incluyendo volúmenes: `make down-v && make up` (vuelve a correr `/docker-entrypoint-initdb.d`).

Fases Postgres → Cockroach: [`docs/fases-postgres-cockroach.md`](docs/fases-postgres-cockroach.md).

## Archivos importantes

| Ruta | Rol |
| --- | --- |
| `docker-compose.yml` | Red, postgres, app, perfiles `lab1`, `lab2` y `lab3` |
| `db/init/` | Schema + CSV → initdb |
| `transactions/` | Pipeline ACID (TEMP TABLE + `transaction()`) |
| `Makefile` | Targets genéricos de entorno + atajos de lab |

## Fallos comunes

| Síntoma | Qué hacer |
| --- | --- |
| init no carga CSV | `make down-v && make up` |
| `connection refused` | `make up` y esperar; repetir `pg_isready` |
| Puerto 5433 ocupado | `POSTGRES_PORT=5434 make up` o `.env` |
| `ModuleNotFoundError: psycopg` en el host | Use `compose run` / `make shell`; no el Python del host |
| CRDB “already initialized” | Normal tras el primer `lab1-up` |
| Mongo `NotYetInitialized` | Falta `rs.initiate()` (Lab 3, Paso 2) |
