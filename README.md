# Instituto Tecnológico de Costa Rica
## TI-4601 Bases de Datos Avanzados — entorno de estudiantes

Entorno alineado a `bigdataclass/`:

1. **Imagen de trabajo** (`Dockerfile`) — Python + `psycopg` (sin Spark).
2. **Postgres oficial** (`scripts/up.sh`) — `127.0.0.1:5433`, sin Compose ni volumes.
3. **`transactions/`** — pipeline SQL contra Postgres (vía Docker).

Copyright: Instituto Tecnológico de Costa Rica.

---

## Camino oficial (usar este)

```bash
git clone <url-de-este-repo> ti4601
cd ti4601
chmod +x *.sh scripts/*.sh transactions/*.sh
./build_image.sh
make verify
```

Éxito: varios `[OK]`, smoke test `answer` con John/Jane, y mensaje «Entorno listo».

**No ejecute** `transactions/*.sh` directamente en el host: hace falta `psycopg` y la
configuración de red correcta. Use `make test-tx` o `./run_image.sh`.

### Equivalente desglosado

```bash
./build_image.sh
./scripts/up.sh                 # postgres:16 en 127.0.0.1:5433
./scripts/load_db.sh            # esquema + COPY de CSV
make test-tx                    # read→…→answer dentro de Docker
./scripts/down.sh               # apaga/borra Postgres (datos efímeros)
```

### Shell interactivo (opcional)

```bash
./scripts/up.sh && ./scripts/load_db.sh
./run_image.sh
# dentro del contenedor ti4601:
cd transactions && ./read.sh && ./answer.sh
```

Salida esperada de `answer`:

```text
customer_id | name | date | adjusted_amount
--------------------------------------------------
1 | John | 2020-03-01 | 108000.0
1 | John | 2020-03-02 | 57600.0
1 | John | 2020-03-03 | 76800.0
2 | Jane | 2020-03-01 | 900.0
2 | Jane | 2020-03-03 | 49.5
```

## Credenciales Postgres

| Parámetro | Valor |
| --- | --- |
| Desde su máquina (`psql`) | `127.0.0.1:5433` |
| Desde contenedores del curso | host `ti4601-postgres`, puerto `5432` (red Docker `ti4601`) |
| Usuario / contraseña / BD | `ti4601` |
| Puerto publicado en el host | `5433` (`POSTGRES_PORT` para cambiarlo) |

## Qué hace `make test-tx` (Docker)

Por cada paso (`read`, `transform`, `aggregate`, `join`, `answer`) equivale a:

```bash
docker run --rm \
  --network ti4601 \
  -e PGHOST=ti4601-postgres \
  -e PGPORT=5432 \
  -e PGUSER=ti4601 \
  -e PGPASSWORD=ti4601 \
  -e PGDATABASE=ti4601 \
  -v "$PWD":/src -w /src/transactions \
  ti4601 python3 read.py
```

## Piezas

| Ruta | Rol |
| --- | --- |
| `Dockerfile` + `build_image.sh` / `run_image.sh` | Imagen `ti4601` |
| `scripts/up.sh` / `down.sh` | Subir / borrar Postgres |
| `scripts/load_db.sh` | Carga CSV → tablas |
| `scripts/test_transactions.sh` | E2E (`make test-tx`) |
| `make verify` | Entorno + smoke test |
| `transactions/*.csv` | Semilla solo para `load_db` |

## Fallos comunes

| Síntoma | Qué hacer |
| --- | --- |
| `docker` FAIL | Arrancar Docker Engine / Desktop |
| Puerto ocupado | `POSTGRES_PORT=5434 ./scripts/up.sh` (y el mismo valor en `make test-tx`) |
| Contenedor viejo / puerto distinto | `./scripts/down.sh` y otra vez `./scripts/up.sh` |
| `connection refused` | `./scripts/down.sh && ./scripts/up.sh && ./scripts/load_db.sh` |
| Firewall (Fedora) | El puerto solo escucha en `127.0.0.1`; el pipeline usa red Docker |
| `ModuleNotFoundError: psycopg` en el host | Normal: use Docker, no Python del host |
| Build lento | Primera vez descarga `python:3.12-slim` / `postgres:16` |
