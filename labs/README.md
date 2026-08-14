# Labs TI-4601 — índice para el estudiante

Cada laboratorio tiene su carpeta con **teoría previa**, **qué observar**, **qué medir**,
**cómo leer el código** y **rúbrica**. No empiecen el experimento sin la teoría de esa
semana (o la semana anterior, si el plan lo indica).

| Carpeta | Plan | Semana práctica | Motor | Teoría antes del lab |
| --- | --- | --- | --- | --- |
| [`lab0-concurrency/`](lab0-concurrency/) | Actividad (no es Lab 1 oficial) | **S3** | Postgres | Aislamiento / lost update (**S2** B3) |
| [`lab1-cluster/`](lab1-cluster/) | **Laboratorio 1** | **S5** | Cockroach ×3 | Raft oral + asignación/geo + semi-join ancla (S5 B1–B3) |
| [`lab2-queries/`](lab2-queries/) | **Laboratorio 2** | **S7** | Cockroach (mismo Lab 1) | Localización/costo (S4) + semi-join (S5); Bernstein (S7) |

## Orden

```text
S2  teoría aislamiento (+ smoke Compose)
S3  Lab 0 + P1 kickoff
S4  fragmentación + prep métricas Lab 2
S5  Raft + semi-join teoría → Lab 1
S7  Lab 2 (planes / bytes / semi-join medido)
```

## Cómo correr código

```bash
# Postgres (lab0):
docker compose run --rm app python3 labs/lab0-concurrency/stress.py …

# Cockroach (lab1 / lab2):
docker compose --profile lab1 run --rm app-crdb python3 labs/lab1-cluster/measure_latency.py
```

Makefile: [`lab1-cluster/README-makefile.md`](lab1-cluster/README-makefile.md).
