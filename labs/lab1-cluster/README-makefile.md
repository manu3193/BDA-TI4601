# Makefile del curso — referencia (Lab 1 / entorno)

Esta página explica los targets del `Makefile` en la raíz del repo. El Lab 1
(`README.md` de esta carpeta) usa los targets `lab1-*`; Lab 0 (S3) usa `up` / `build` /
`lab-concurrency`. Índice: [`../README.md`](../README.md).

El Makefile es la **interfaz operativa** de entorno (genérica). Los smoke tests de cada
lab se documentan en su README y se corren a mano con `docker compose run`.

## Idea central

| Capa | Qué es |
| --- | --- |
| `Makefile` | Atajos de entorno (`make up`, `make shell`, …) |
| `docker compose` | Orquestación (servicios, red, `PG*`) |
| Servicio `app` | Imagen Python + `psycopg`; monta el repo en `/src` |
| Servicio `postgres` | Motor S2–S4 (volumen + initdb) |
| Perfil `lab1` | Cockroach ×3 + `app-crdb` (S5 / P1) |

Correr Python en el curso = siempre:

```bash
docker compose run --rm app python3 <script.py>
```

## Verificar el entorno (manual — no hay `make verify`)

```bash
make up
make build
docker compose exec -T postgres pg_isready -U ti4601 -d ti4601
docker compose run --rm app python3 transactions/answer.py
# Esperado: filas John y Jane
```

Ese último comando es el modelo para labs y P1.

## Targets — entorno Postgres (S2–S4)

| Target | Qué hace |
| --- | --- |
| `make help` | Lista comandos |
| `make up` | `docker compose up -d postgres` |
| `make down` | Apaga servicios (`--remove-orphans`) |
| `make down-v` | Apaga y **borra volúmenes** → re-seed en el próximo `up` |
| `make build` | Construye imagen `ti4601:local` |
| `make shell` | `up` + bash en `app` (PG* inyectadas) |
| `make reset-pg` | `down-v` + `up` |
| `make test-tx` | Pipeline `read→…→answer` vía `compose run` |
| `make lab-concurrency` | `labs/lab0-concurrency/stress.py` en `app` |

```bash
make lab-concurrency ISOLATION=SERIALIZABLE WORKERS=60 RETRIES=12
```

## Targets — Lab 1 / P1 (perfil `lab1`, S5+)

| Target | Qué hace |
| --- | --- |
| `make lab1-up` | Sube `crdb-1|2|3` + `crdb-init` |
| `make lab1-down` | Apaga lab1 (conserva volúmenes) |
| `make lab1-down-v` | Apaga y borra volúmenes CRDB |
| `make lab1-shell` | Shell en `app-crdb` |

Procedimiento del lab: [`README.md`](README.md).

```bash
make lab1-up
docker compose --profile lab1 run --rm app-crdb python3 -c "import psycopg; …"
```

## Mapa mental: un script nuevo

1. Escriba `mi_lab/foo.py` con `psycopg.connect()` (libpq / `PG*`).  
2. No hardcodee hosts.  
3. Ejecute:

```bash
make up
docker compose run --rm app python3 mi_lab/foo.py
# Lab 1:
docker compose --profile lab1 run --rm app-crdb python3 mi_lab/foo.py
```

## Qué no hacer

- Instalar `psycopg` en el host “porque el smoke pasó”.  
- Mezclar Postgres (`make up`) con el clúster Raft.  
- `make lab1-up` en S3 como entrega del kickoff P1.  
- Borrar volúmenes (`down-v`) a mitad de una medición sin anotarlo.

## Archivos relacionados

| Ruta | Rol |
| --- | --- |
| `/Makefile` | Targets de entorno |
| `/docker-compose.yml` | Servicios y perfiles |
| `/README.md` | Verificación manual + patrón Compose |
| `/docs/fases-postgres-cockroach.md` | Fases A→C |
| `README.md` (esta carpeta) | Procedimiento Lab 1 |
