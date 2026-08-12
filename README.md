# Instituto Tecnológico de Costa Rica
## TI-4601 Bases de Datos Avanzados — entorno de estudiantes

Entrega **Semana 2**:

1. **Imagen de trabajo** (`Dockerfile`) — Python + `psycopg` (sin Spark).
2. **Postgres oficial** (`scripts/up.sh`) — almacena y consulta el ejemplo.
3. **`transactions/`** — read→transform→aggregate→join→answer **contra Postgres**.

Copyright: Instituto Tecnológico de Costa Rica.

---

## Requisitos

- Docker Engine en ejecución
- Git
- ~1 GB libres para imágenes (`python:3.12-slim`, `postgres:16`)

## Pasos de inicio a fin (validado)

```bash
git clone <url-de-este-repo> ti4601
cd ti4601
chmod +x *.sh scripts/*.sh transactions/*.sh

# 1) Imagen de trabajo (Python + psycopg)
./build_image.sh

# 2) Verificación completa: Postgres + carga de datos + pipeline transactions
make verify
```

`make verify` debe terminar con `7 OK, 0 FAIL` y mostrar el resultado de `answer`
(p. ej. John / 108000.0, Jane / 900.0).

### Equivalente paso a paso (sin `make verify`)

```bash
./build_image.sh
./scripts/up.sh              # postgres:16 en localhost:5433
./scripts/load_db.sh         # esquema + COPY de los CSV
make test-tx                 # read → transform → aggregate → join → answer
```

### Paso a paso manual dentro de la imagen

```bash
./scripts/up.sh
./scripts/load_db.sh
./run_image.sh
```

Dentro del contenedor `ti4601`:

```bash
cd transactions
./read.sh
./transform.sh
./aggregate.sh
./join.sh
./answer.sh
```

Salida esperada de `./answer.sh`:

```text
customer_id | name | date | adjusted_amount
--------------------------------------------------
1 | John | 2020-03-01 | 108000.0
1 | John | 2020-03-02 | 57600.0
1 | John | 2020-03-03 | 76800.0
2 | Jane | 2020-03-01 | 900.0
2 | Jane | 2020-03-03 | 49.5
```

### Apagar

```bash
./scripts/down.sh            # elimina el contenedor Postgres (datos efímeros)
```

**No es Lab 1.** Tarea 1 (Abadi) se entrega por TEC Digital.

## Credenciales Postgres

| Parámetro | Valor |
| --- | --- |
| Host (desde su máquina) | `localhost` |
| Host (desde `run_image.sh`) | `host.docker.internal` |
| Puerto | `5433` |
| Usuario / contraseña / BD | `ti4601` |

## Piezas Docker (como Big Data)

| Pieza | Rol |
| --- | --- |
| `Dockerfile` + `build_image.sh` / `run_image.sh` | Imagen de trabajo `ti4601` |
| `scripts/up.sh` / `down.sh` | Subir / borrar `postgres:16` (sin Compose ni volumes) |
| `scripts/load_db.sh` | Carga CSVs en Postgres |
| `scripts/test_transactions.sh` | Prueba end-to-end (`make test-tx`) |
| `make verify` | Chequeo de entorno + smoke test |

## Contenido

| Ruta | Rol |
| --- | --- |
| `transactions/*.py` | Consultas SQL progresivas vía `psycopg` |
| `db/initialize.sql` | Esquema |
| `transactions/*.csv` | Semilla para `load_db` |

## Fallos comunes

| Síntoma | Qué hacer |
| --- | --- |
| `docker` FAIL | Arrancar Docker Desktop / Engine |
| Puerto 5433 ocupado | `POSTGRES_PORT=5434 ./scripts/up.sh` y el mismo valor en el entorno al correr el pipeline |
| Build lento | Primera vez descarga imágenes base; reintentar |
| `connection refused` desde `run_image.sh` | Verificar `./scripts/up.sh` y que Postgres responda en `:5433` |
