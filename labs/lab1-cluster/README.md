# Lab 1 — Clúster CockroachDB: quórum, rangos, geo y falla de nodo

**Semana:** 5 · **Peso:** 3 % · On-ramp del **Proyecto 1**  
**No confundir con** [`../lab0-concurrency/`](../lab0-concurrency/) (S3 práctica, un nodo Postgres).

**Teoría previa (misma semana, antes del laboratorio):**

1. Oral / clase **Raft** (líder, término, quórum de mayoría, log replicado).  
2. Asignación de fragmentos + **geo / residencia** (material 04-II).  
3. Recordatorio S3: shared-nothing + consenso = familia Cockroach.

Índice: [`../README.md`](../README.md) · Makefile: [`README-makefile.md`](README-makefile.md).

---

## 1. Para qué sirve (aprendizaje)

Van a **ver** lo que el paper de Raft describe con palabras: sin mayoría no hay decisión;
con mayoría el sistema sigue aceptando escrituras aunque un nodo muera.

| Concepto de clase | Qué lo evidencia el lab |
| --- | --- |
| Shared-nothing + consenso | 3 procesos `crdb-*`, UI `:8080`, `node status` |
| Quórum \( \lceil N/2\rceil+1 \) (N=3 → 2) | Chaos A (1 down) escribe; Chaos B (2 down) no |
| Líder Raft / rangos | `SHOW RANGES` / UI; commits pasan por réplica del rango |
| Residencia / shard key (S4–P1) | Columna `region` o `REGIONAL BY ROW` + justificación |
| Latencia de commit | `measure_latency.py` → p50 |
| PACELC | En falla (P): priorizan C+quórum (no escriben sin mayoría) |
| Cliente del curso | Mismo `psycopg`; solo cambian `PG*` (`app-crdb`) |

---

## 2. Modelo mental

```text
        ┌─ crdb-1 ─┐
cliente─┤  crdb-2  ├─ réplicas Raft por rango
        └─ crdb-3 ─┘
```

- **1 nodo caído:** quedan 2/3 → hay quórum → `UPSERT` debe confirmar (quizá más lento).  
- **2 nodos caídos:** queda 1/3 → no hay quórum → el `UPSERT` **no** confirma (timeout).  
Eso no es “Docker lento”: es el protocolo negándose a romper consistencia de consenso.

---

## 3. Qué datos recolectar

### Tabla 1 — Clúster sano

| Campo | Valor | Evidencia |
| --- | --- | --- |
| Hora `lab1-up` | | |
| Nodos `is_live=true` | /3 | `evidence/01-nodes.txt` |
| UI accesible :8080 | sí/no | nota |

### Tabla 2 — Rangos / geo

| Campo | Valor | Evidencia |
| --- | --- | --- |
| Salida `SHOW RANGES FROM TABLE ping` (o equivalente) | pegar resumen | `02-ranges.txt` |
| ¿Multi-region nativo OK o fallback columna `region`? | nativo / fallback | `03-geo.txt` |
| Conteo por región | r1= _ r2= _ r3= _ | `03-geo.txt` |
| Shard key del P1 (1 frase) | | informe |

### Tabla 3 — Latencia

| Campo | Valor | Evidencia |
| --- | --- | --- |
| n commits | 30 (default script) | `04-latency.txt` |
| p50_ms | | |
| p90_ms | | |
| Interpretación (1–2 frases) | p.ej. commit local en lab sin RTT WAN | informe |

### Tabla 4 — Chaos

| Experimento | Nodos down | ¿UPSERT confirmó? | Tiempo percibido | Evidencia |
| --- | --- | --- | --- | --- |
| A (obligatorio) | 1 (`crdb-2`) | sí/no | t0→t1 | `05-chaos-a.txt` |
| B (bonus) | 2 | sí/no / timeout | | `06-chaos-b.txt` |

**Comparaciones obligatorias en el informe:**

1. Chaos A vs B: ¿por qué cambia el resultado? (quórum 2 vs 1).  
2. Relacione con Raft: “hace falta mayoría de réplicas del rango/raft group”.  
3. PACELC: en partición/falla grave el sistema **no** elige A a costa de C de consenso.  
4. Latencia: un número sin método no cuenta; cite n y el script.

---

## 4. Qué observar según el resultado

| Resultado | Interpretación correcta | Interpretación incorrecta |
| --- | --- | --- |
| A: escritura OK con 1 down | Quórum 2/3; disponibilidad parcial | “Cockroach no usa consenso” |
| B: timeout con 2 down | Sin mayoría no hay commit | “Se cayó Docker / red mala” sin más |
| `node status` aún muestra live un rato | Heartbeats tardan; mire el UPSERT | Confiar solo en la columna live |
| p50 alto tras chaos | Reelección / rebalance | Ignorar y no reportar |
| Multi-region falla en insecure local | Usar fallback + explicar mapeo a P1 | Inventar localities falsas |

---

## 5. El código — qué hace cada pieza

### 5.1 Orquestación (no es Python)

| Pieza | Rol |
| --- | --- |
| `make lab1-up` | Sube 3 nodos + `crdb-init` (crea BD `ti4601`) |
| `app-crdb` en Compose | Mismo Dockerfile; `PGHOST=crdb-1` `PGPORT=26257` `PGSSLMODE=disable` |
| `docker stop ti4601-crdb-2` | Chaos de **proceso** (falla de sitio simplificada) |

### 5.2 `measure_latency.py` (léanlo línea a línea)

| Bloque | Qué hace | Por qué importa |
| --- | --- | --- |
| `psycopg.connect()` | Usa `PG*` del contenedor | Mismo patrón que Lab 0 / `transactions/` |
| `CREATE TABLE IF NOT EXISTS ping` | Tabla mínima de prueba | Independiente del dominio P1 al inicio |
| Bucle `N=30` | Cada iteración: `transaction` + `UPSERT` | Una muestra = un commit |
| `time.perf_counter()` | Mide solo el commit redondo | Método reproducible |
| `statistics.median` → p50 | Robustez ante outliers | Reporten p50 (y p90 si quieren) |

No es un benchmark de producción: es **evidencia metodológica** para el informe y el P1.

### 5.3 SQL que ejecutan a mano

- `cockroach node status` → membresía del clúster.  
- `SHOW RANGES FROM TABLE ping` → fragmentos/rangos (vocabulario industrial del lab).  
- `UPSERT` bajo chaos → disponibilidad de escritura.

---

## 6. Procedimiento guiado

### 6.0 Antes de encender Docker

Checklist teórico (márquelo):

- [ ] Sé definir quórum para N=3.  
- [ ] Sé decir qué es un líder Raft en una frase.  
- [ ] Tengo el shard key del P1 en una frase (S4).  

Si algún ítem falla: **no empiecen el chaos**; vuelvan a la clase/oral Raft.

### Parte A — Levantar

```bash
make lab1-up
docker compose --profile lab1 ps
docker exec ti4601-crdb-1 cockroach node status --insecure | tee evidence/01-nodes.txt
```

**Observe:** 3 filas live. UI http://127.0.0.1:8080

### Parte B — Tabla + rangos

```bash
docker exec ti4601-crdb-1 cockroach sql --insecure -d ti4601 -e "
CREATE TABLE IF NOT EXISTS ping (
  id INT PRIMARY KEY,
  note STRING,
  region STRING NOT NULL DEFAULT 'r1',
  written_at TIMESTAMPTZ DEFAULT now()
);
UPSERT INTO ping (id, note, region) VALUES (1, 'antes-de-chaos', 'r1');
SHOW RANGES FROM TABLE ping;
" | tee evidence/02-ranges.txt
```

**Observe:** al menos un rango; anote lo que entiendan (leaseholder/réplicas si aparece).

### Parte C — Geo / residencia

Intenten regiones nativas si su versión lo permite. Si no:

```sql
UPSERT INTO ping (id, note, region) VALUES
  (1, 'sj', 'r1'), (2, 'limon', 'r2'), (3, 'us', 'r3');
SELECT region, count(*) FROM ping GROUP BY region;
```

Guarden en `evidence/03-geo.txt`. En el informe: cómo esto se vuelve `REGIONAL BY ROW` en el P1.

### Parte D — Latencia

```bash
docker compose --profile lab1 run --rm app-crdb \
  python3 labs/lab1-cluster/measure_latency.py | tee evidence/04-latency.txt
```

**Observe:** orden de magnitud de p50 (ms). Compárenlo mentalmente con un `UPSERT` en Postgres local de S2 (no hace falta repetir; cualitativo).

### Parte E — Chaos A (1 nodo)

```bash
date --iso-8601=seconds | tee evidence/05-chaos-a.txt
docker stop ti4601-crdb-2
docker exec ti4601-crdb-1 cockroach sql --insecure -d ti4601 -e "
UPSERT INTO ping (id, note) VALUES (1, 'despues-de-matar-un-nodo');
SELECT id, note FROM ping;
" | tee -a evidence/05-chaos-a.txt
date --iso-8601=seconds | tee -a evidence/05-chaos-a.txt
docker start ti4601-crdb-2
```

**Observe:** ¿confirmó? Complete Tabla 4. Relacione con quórum.

### Parte F — Chaos B (bonus)

```bash
docker stop ti4601-crdb-2 ti4601-crdb-3
timeout 15 docker exec ti4601-crdb-1 cockroach sql --insecure -d ti4601 -e \
  "UPSERT INTO ping (id, note) VALUES (1, 'sin-quorum');" \
  | tee evidence/06-chaos-b.txt \
  || echo "timeout sin quórum (esperado)" | tee -a evidence/06-chaos-b.txt
docker start ti4601-crdb-2 ti4601-crdb-3
```

**Observe:** timeout ≈ evidencia de “sin mayoría”.

### Parte G — Cliente Python

```bash
docker compose --profile lab1 run --rm app-crdb python3 -c "
import psycopg
with psycopg.connect() as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute('SELECT id, note, region FROM ping ORDER BY id')
            print(cur.fetchall())
"
```

---

## 7. Entregable

1. `evidence/01`…`06` (B opcional).  
2. Informe con tablas §3 + secciones:

| Sección | Extensión |
| --- | --- |
| Resultados (tablas) | 1–2 pág |
| Raft ↔ chaos | ½–1 pág |
| Geo ↔ shard key P1 | ½ pág |
| Latencia (método + p50) | ¼–½ pág |
| PACELC | 3–5 frases |
| Código / cliente | ¼ pág (`measure_latency` + PG*) |

## 8. Rúbrica

| Criterio | 100 | 50 | 0 |
| --- | --- | --- | --- |
| Datos tablas 1–4 | Completas + evidence | Parcial | Sin números |
| Chaos A interpretado con quórum | Sí | “Siguió / no siguió” | Omitido |
| Raft | Términos del paper ↔ lab | Vocabulario vago | No |
| Geo / P1 | Enlace shard key | Solo SQL | No |
| Latencia | p50 + método | Solo p50 | No |

## Apagar

```bash
make lab1-down
# make lab1-down-v   # borra volúmenes del clúster
```
