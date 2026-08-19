# Lab 0 — Concurrencia: Lost Update vs SERIALIZABLE

**Semana 3:**
**Motor:** Postgres (`make up`).  

Índice: [`../README.md`](../README.md).

---

## 1. Objetivo

Van a **provocar** una anomalía en la base de datos, y luego van a ver ver cómo el
motor la evita subiendo el aislamiento, a costa de abortar transacciones.

| Concepto de clase | Qué lo evidencia el experimento |
| --- | --- |
| Lost update | Bajo RC: muchos commits “OK” pero el saldo casi no baja |
| READ COMMITTED (default Postgres) | No logra detectar la condición de carrera de Read-Modify-Write (RMW) en el cliente |
| SERIALIZABLE | Aparecen `SerializationFailure`; el saldo cuadra con los OK |
| Reintentos / backoff | El cliente debe manejar aborts (no “se rompió la BD”) |
| PACELC (puente) | Esto es **un nodo** en operación normal: tradeoff L vs C de *aislamiento*, a este momento no hemos explorado aun el particionamiento de red |

---

## 2. Modelo mental del experimento

Saldo inicial: **1000**. Cada worker intenta restar 1 con este anti-patrón:

```text
BEGIN
  balance ← SELECT balance FROM accounts WHERE id = 1
  sleep(2 ms)          ← ventana artificial para maximizar carrera
  UPDATE accounts SET balance = balance_leído - 1
COMMIT
```

Si 40 workers tuvieran efecto atómico cada uno, el saldo final sería **960**.

- Si el saldo queda **cerca de 1000** con 40 OK → muchas transacciones se **perdieron** (lost update).  
- Si el saldo es **1000 − (# OK)** → cada OK logró modificar el balance; los que generaron condiciones de carrera fueron abortados.

---

## 3. Qué datos recolectar ( deben generar una tabla obligatoria)

Corra **dos** experimentos con el mismo `WORKERS` (recomendado 40). Complete:

| Métrica | Símbolo | READ COMMITTED | SERIALIZABLE | Cómo leerla |
| --- | --- | --- | --- | --- |
| Workers lanzados | $\(W\)$ | | | parámetro |
| Commits OK | $\(OK\)$ | | | línea del script |
| SerializationFailure | $\(SF\)$ | | | línea del script (suele ser 0 en RC) |
| Otros errores | | | | debe ser ~0 |
| Saldo final | $\(S\)$ | | | línea del script |
| Esperado si cada OK −1 | $\(E = 1000 - OK\)$ | | | lo imprime el script |
| Lost updates (aprox.) | $\(L \approx S - E\)$ si $\(S > E\)$ | | | en RC suele ser ≫ 0 |
| ¿$\(S \approx E\)$? | | | | RC: no · SER: sí |

**Comparaciones que deben escribir en el informe:**

1. $\(S_{RC}\)$ vs $\(E_{RC}\)$: si \(S_{RC} \gg E_{RC}\), hubo lost update.  
2. $\(SF_{RC}\)$ vs $\(SF_{SER}\)$: en SER debe dispararse.  
3. $\(S_{SER}\)$ vs $\(E_{SER}\)$: deben coincidir (salvo `otros errores` o retries agotados).  
4. $\(OK_{SER}\)$ vs $\(W\)$: con retries finitos, a veces $\(OK < W\)$; eso también es dato.

Guarden salidas crudas: `evidence/rc.txt` y `evidence/serializable.txt`.

---

## 4. Qué observar según el resultado (guía de interpretación)

### Escenario A — READ COMMITTED (típico)

```text
Commits OK: 40
SerializationFailure: 0
Saldo final: ~998
Esperado si cada OK −1: 960
```

**Explicación:** varios workers leyeron el mismo 1000 (o el mismo valor intermedio),
esperaron, y escribieron `valor−1`. El último en hacer COMMIT gana; las restas
anteriores se pierden. Por eso hay 40 commits exitosos pero el saldo casi no baja.
**No** es que Postgres “mienta”: RC **no promete** serializar ese patrón RMW.

### Escenario B — SERIALIZABLE (típico)

```text
Commits OK: ~25–40
SerializationFailure: decenas o cientos
Saldo final: 1000 − OK
```

**Explicación:** el motor detecta que el historial no es equivalente a un orden serial y
aborta. El código captura `SerializationFailure` y reintenta. Cada OK que queda
corresponde a una resta que “sobrevivió”; por eso \(S = 1000 - OK\).

### Escenarios anómalos (qué revisar)

| Síntoma | Causa probable |
| --- | --- |
| RC con $\(S \approx E\)$ | Poca concurrencia efectiva (baje sleep / suba workers) o corrida rara |
| SER con $\(S \neq E\)$ | Retries agotados (`otros errores` o SF altos y OK bajos) → suba `RETRIES` |
| `connection refused` | No hizo `make up` / usó Python del host |

---

## 5. El código (`stress.py`) — guía de lectura

No reescriban el script; deben **explicarlo** en el informe (½ pág).

| Función / bloque | Qué hace | Concepto |
| --- | --- | --- |
| `connect()` | `psycopg.connect()` sin host fijo; usa `PG*` de Compose | Cliente del curso |
| `reset_account()` | Deja `balance = 1000` antes de cada ráfaga | Estado inicial controlado |
| `conn.isolation_level = …` | Fija RC o SERIALIZABLE **antes** del `transaction()` | Nivel de aislamiento |
| `SELECT` → `sleep(0.002)` → `UPDATE … balance_leído - 1` | RMW no atómico a propósito | Anti-patrón lost update |
| `except errors.SerializationFailure` | Contador \(SF\) + reintento | Abort serializable |
| `delay = 2^(attempt-1) * … + jitter` | Backoff exponencial | Evitar thundering herd |
| `threading.Thread` × `WORKERS` | Ráfaga concurrente real | Carrera |
| `E = 1000 - OK` vs `S` | Atomicidad aparente | Qué comparar |

Fragmento central (idea):

```python
conn.isolation_level = isolation
with conn.transaction():
    cur.execute("SELECT balance FROM accounts WHERE id = %s", …)
    balance = cur.fetchone()[0]
    time.sleep(0.002)  # agranda la ventana de carrera
    cur.execute("UPDATE accounts SET balance = %s …", (balance - 1, …))
```

---

## 6. Procedimiento 

### 6.1 Entorno

```bash
make up && make build
docker compose exec -T postgres pg_isready -U ti4601 -d ti4601
docker compose run --rm app python3 transactions/answer.py   # smoke John/Jane
```

### 6.2 Experimentos

```bash
make lab-concurrency ISOLATION=READ_COMMITTED    # → evidence/rc.txt
make lab-concurrency ISOLATION=SERIALIZABLE      # → evidence/serializable.txt
```

Equivalente:

```bash
docker compose run --rm app python3 labs/lab0-concurrency/stress.py \
  --isolation READ_COMMITTED --workers 40 --retries 8
```

### 6.3 Informe

1. Tabla de la sección 3 completa.  
2. Debe discutir las condiciones de carrera encontradas: por qué $\(S \gg E\)$ (o por qué no, si no salió).  
3. Debe discutir la serialización aplicada y su efecto: rol de $\(SF\)$ y por qué $\(S \approx E\)$.  
4. Debe explicar el código: explique el RMW + isolation + retry.  

---

## 7. Rúbrica

| Criterio | Puntaje |
| --- | --- |
| Datos sección 3 | Ambos aislamientos + \(S\) vs \(E\) | 30 pts |
| Informe | 35pts | |
| Evidencia en txt | 15pts |

