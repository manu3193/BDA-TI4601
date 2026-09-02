# Labs TI-4601 — índice para el estudiante

Cada laboratorio tiene su carpeta con **teoría previa**, **qué observar**, **qué medir**,
**cómo leer el código** y **rúbrica**. No empiecen el experimento sin la teoría de esa
semana (o la semana anterior, si el plan lo indica).

Los **seis** labs (0 a 5) son calificados: **2,5 %** cada uno (15 % del curso). Las
carpetas no se renumeran.

| Carpeta | Plan | Semana práctica | Motor | Teoría antes del lab |
| --- | --- | --- | --- | --- |
| [`lab0-concurrency/`](lab0-concurrency/) | **Laboratorio 0** (2,5 %) | **S3** | Postgres | Aislamiento / lost update (**S2** B3) |
| [`lab1-cluster/`](lab1-cluster/) | **Laboratorio 1** (2,5 %) | **S5** | Cockroach ×3 | Raft oral + mapa 04-II → CRDB (`REGIONAL BY ROW`) |
| [`lab2-queries/`](lab2-queries/) | **Laboratorio 2** (2,5 %) | **S7** | Cockroach (mismo Lab 1) | Localización (S4) + PPTX 05 (S6) + Bernstein / semi-join (S7) |
| *(se publica S10)* | **Laboratorio 3** (2,5 %) | **S10** | Cockroach | 2PC / Spanner (S9–S10); partición de red |
| *(se publica S13)* | **Laboratorio 4** (2,5 %) | **S13** | DuckDB + Iceberg + MinIO | Temporal (S12); adelanta U8 (S14) |
| *(se publica S15)* | **Laboratorio 5** (2,5 %) | **S15** | pgvector + federación/CDC | HNSW (S13) + NoSQL (S15) |

Si alguna carpeta aún no está publicada, el enunciado aparece esa semana en TEC Digital /
esta misma ruta.

## Orden

```text
S2  teoría aislamiento (+ smoke Compose)
S3  Lab 0 (calificado)
S4  asignación P1 + fragmentación + prep métricas Lab 2
S5  Raft + geo/`REGIONAL BY ROW` → Lab 1
S6  procesamiento de consultas (PPTX 05) + Neumann
S7  Lab 2 (planes / bytes / semi-join medido)
S8  Parcial I + defensa P1
S10 Lab 3 + asignación P2
S13 Lab 4 + hito P2 stack A
S15 Lab 5 + hito P2 stack B
S16 Parcial II + defensa P2
```

## Cómo correr código

```bash
# Postgres (lab0):
docker compose run --rm app python3 labs/lab0-concurrency/stress.py …

# Cockroach (lab1 / lab2):
make lab1-up
make lab1-status
# Configuración, medición y falla se ejecutan paso a paso:
# labs/lab1-cluster/README.md
make lab1-check
```

Guía completa y comandos: [`lab1-cluster/README.md`](lab1-cluster/README.md).
