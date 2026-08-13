# Fases del entorno — Postgres → CockroachDB (P1)

## El problema pedagógico

El Proyecto 1 exige un clúster con consenso (CockroachDB), pero ese motor se
estudia con rigor en **Lab 1 (S5)** y U5. Asignar P1 en S3 **no** implica usar
Cockroach en S3.

## Solución: tres fases, un mismo cliente Python

```text
S2–S4  Fase A · postgres     diseño P1 + ACID + lab concurrencia
S5     Fase B · lab1 (CRDB)  primer contacto guiado (Lab 1 = on-ramp)
S5–S8  Fase C · lab1 (CRDB)  construcción y mediciones del P1
```

| Fase | Compose | Qué hacen | Qué no hacen |
| --- | --- | --- | --- |
| **A** | `make up` (Postgres + volumen) | Pipeline `transactions/`, lab concurrencia, **diseño** P1 (E1), prototipo de esquema en SQL portable | Montar Raft / matar nodos |
| **B** | `make lab1-up` | Lab 1: 3 nodos, localities, latencia, falla de nodo **con guía** | Entregar P1 completo el mismo día |
| **C** | mismo `lab1` | P1 E2–E5 sobre el clúster ya conocido | Cambiar de motor sin aprobación |

El código Python habla el **wire protocol Postgres** (`psycopg`). Solo cambian
`PGHOST` / `PGPORT` / `PGUSER` inyectados por Compose (`app` vs `app-crdb`).

## Contrato SQL portable (prototipo en A, producción en C)

Usen en el diseño P1 un subconjunto que corra en ambos motores:

- Tipos: `INT`, `NUMERIC`, `TEXT`, `TIMESTAMPTZ` / `TIMESTAMP`, `BOOL`
- PK / FK / `CHECK` simples
- `INSERT` / `UPDATE` / `SELECT` / agregaciones
- Evitar en el prototipo A: `COPY` propietario, extensiones (`pgvector`), CTEs
  recursivos raros, `LISTEN/NOTIFY`

Locality / `REGIONAL BY ROW` **solo en Fase B–C** (tras Lab 1).

## Chaos (Fase B–C, no A)

```bash
make lab1-up
# … carga / escritura de prueba …
docker stop ti4601-crdb-2
# medir tiempo hasta nueva escritura OK (RTO)
docker start ti4601-crdb-2
```

Documenten quórum (2 de 3) y relacionen con CAP/PACELC. Partición de red
completa = bonus P1 (U5/Lab 3).

## Reset de datos

- Postgres (init otra vez): `make down-v` luego `make up`
- Cockroach: `make lab1-down-v` luego `make lab1-up`
