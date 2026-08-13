# Lab 1 — Clúster CockroachDB: quórum, rangos y falla de nodo

**Semana:** 5 · **Peso:** 3 % (labs) · **On-ramp del Proyecto 1**  
**Lectura de la semana:** Ongaro & Ousterhout, *Raft* (obligatoria para el oral y para
interpretar este lab).

## Objetivos

Al terminar deben poder:

1. Levantar y describir un clúster shared-nothing de 3 nodos (`make lab1-up`).
2. Explicar por qué con **1 nodo caído** aún hay escrituras (quórum 2/3) y con **2 caídos** no.
3. Relacionar lo observado con **líder Raft / término / quórum** (paper de la semana).
4. Dejar el stack listo para el P1 (mismo `psycopg`, `PG*` → Cockroach).

## Prerrequisitos

| Semana | Concepto |
| --- | --- |
| S2 | PACELC; Postgres Compose (`make up`) |
| S3 | Shared-nothing + consenso; P1 Fase A (diseño) |
| S4 | Shard key / fragmentación (DDIA) |
| S5 (hoy) | Raft (leer **antes** de la sesión de lab) |

**No** usen este perfil en S3. Ver `docs/fases-postgres-cockroach.md`.

## Procedimiento

### 1. Levantar

```bash
cd ti4601   # repo estudiantes
make lab1-up
docker compose --profile lab1 ps
```

Esperado: `ti4601-crdb-1|2|3` Up. UI: http://127.0.0.1:8080

### 2. Estado del clúster

```bash
docker exec ti4601-crdb-1 cockroach node status --insecure
```

Anoten: `id`, `is_available`, `is_live` para los tres.

### 3. Tabla de prueba + escritura

```bash
docker exec ti4601-crdb-1 cockroach sql --insecure -d ti4601 -e "
CREATE TABLE IF NOT EXISTS ping (
  id INT PRIMARY KEY,
  note STRING,
  written_at TIMESTAMPTZ DEFAULT now()
);
UPSERT INTO ping (id, note) VALUES (1, 'antes-de-chaos');
SELECT * FROM ping;
"
```

### 4. Chaos A — un nodo (obligatorio)

```bash
date --iso-8601=seconds
docker stop ti4601-crdb-2
# reintentar UPSERT en crdb-1
docker exec ti4601-crdb-1 cockroach sql --insecure -d ti4601 -e "
UPSERT INTO ping (id, note) VALUES (1, 'despues-de-matar-un-nodo');
SELECT id, note FROM ping;
"
date --iso-8601=seconds
docker start ti4601-crdb-2
```

### 5. Chaos B — dos nodos (demostración / bonus en informe)

```bash
docker stop ti4601-crdb-2 ti4601-crdb-3
# UPSERT con timeout ~15s → no confirma (sin quórum)
timeout 15 docker exec ti4601-crdb-1 cockroach sql --insecure -d ti4601 -e \
  "UPSERT INTO ping (id, note) VALUES (1, 'sin-quorum');" || echo "sin quórum (esperado)"
docker start ti4601-crdb-2 ti4601-crdb-3
# UPSERT de recuperación
```

### 6. Cliente Python del curso

```bash
docker compose --profile lab1 run --rm app-crdb python3 -c "
import psycopg
with psycopg.connect() as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute('SELECT id, note FROM ping')
            print(cur.fetchall())
"
```

### 7. (P1 / extensión de sesión) Residencia

Sobre una tabla del dominio P1 (o ejemplo del lab): localities /
`REGIONAL BY ROW`, y una medición de latencia local vs remota si el docente
habilita latencia inyectada. Detalle en la guía S5 de `lecciones/S05/`.

## Entregable (informe corto)

| Campo | Valor |
| --- | --- |
| Nodos vivos iniciales | |
| Chaos A: ¿escritura OK? | sí/no + hora |
| Chaos B: ¿escritura OK? | sí/no / timeout |
| Relación con Raft (5–8 líneas) | líder, quórum, qué garantiza |
| Enlace PACELC | una frase |

Capturas o pegado de `node status` + salida SQL.

## Apagar

```bash
make lab1-down        # conserva volúmenes
# make lab1-down-v    # borra datos del clúster
```

## Rúbrica rápida

| Criterio | 100 | 50 | 0 |
| --- | --- | --- | --- |
| Clúster reproducible | `lab1-up` + evidencia | Solo captura sin comandos | No corre |
| Chaos A | Escritura con 1 down + explicación quórum | Mentado sin evidencia | Omitido |
| Raft | Usa términos del paper con el experimento | Vocabulario vago | Sin enlace |
| PACELC | Conecta C/A en falla vs operación | Solo eslogan | Ausente |
