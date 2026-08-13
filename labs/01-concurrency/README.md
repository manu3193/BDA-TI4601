# Lab 01 — Concurrencia: Lost Update vs SERIALIZABLE

**Cuándo:** Semana 2 (tras demo ACID / niveles de aislamiento).  
**Motor:** **solo Postgres** del perfil base (`make up`). No use Cockroach aquí:
su aislamiento por defecto es otro y el punto pedagógico se diluye.

## Objetivo

Observar con evidencia numérica:

1. **READ COMMITTED** — anomalía de *lost update* al actualizar la misma fila
   con lectura-modificación-escritura concurrente.
2. **SERIALIZABLE** — el motor aborta con `SerializationFailure`; el cliente
   reintenta con *backoff* exponencial y el saldo converge.

## Cómo correr

```bash
make up
make lab-concurrency ISOLATION=READ_COMMITTED
make lab-concurrency ISOLATION=SERIALIZABLE
```

Opcional: `WORKERS=60 RETRIES=12`.

## Qué entregar (informe corto)

| Campo | RC | SERIALIZABLE |
| --- | --- | --- |
| workers | | |
| commits OK | | |
| SerializationFailure | | |
| saldo final | | |
| ¿hubo lost update? | sí/no + por qué | sí/no + por qué |

En 5–10 líneas: relación con lo visto en clase (Write Skew / Lost Update) y con
PACELC (esto es el nodo; la C de ACID ≠ C de CAP).

## Pista

El script hace `SELECT balance` → `sleep` → `UPDATE balance = balance_leído - 1`.
Eso **no** es `UPDATE balance = balance - 1` atómico en SQL; es el anti-patrón
delicado a propósito.
