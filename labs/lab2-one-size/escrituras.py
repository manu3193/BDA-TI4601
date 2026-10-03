#!/usr/bin/env python3
"""Paso 3 — Escrituras: operaciones puntuales y el experimento del feed del paper.

3a. Operación por llave (terreno OLTP)
    2 000 viajes al azar. Para cada uno, una lectura por llave y un update por
    llave. En Postgres, el update con autocommit espera a que el WAL (la bitácora)
    llegue a disco antes de responder: eso es durabilidad. Valkey, como está
    configurado en el curso, no escribe nada a disco.

3b. El dataset 
    Los primeros N viajes se reproducen como mensajes de un flujo. Cada mensaje:
      - suma 1 al conteo y fare_amount a la suma de su payment_type;
      - si es una anomalía (trip_distance <= 0 o fare_amount <= 0), suma 1 a las
        anomalías de su vendor_id y, cada 100 anomalías de ese proveedor, emite
        una alerta cada --umbral anomalías de ese proveedor (el «Count100» de la
        Figura 6 del paper usa 100; el lab usa 10 por defecto para que 10 000
        mensajes alcancen a disparar alertas y la verificación pruebe esa rama).

    Postgres lo hace «outbound»: guarda el mensaje en feed_trip y un
    trigger actualiza los contadores (sql/pg_feed.sql). Valkey lo hace
    «inbound»: el mensaje no se guarda, solo pasa por un script Lua que corre
    dentro del servidor (lua/feed.lua).

    Seis variantes, para separar cuánto de la diferencia es durabilidad y cuánto
    es el modelo:

        postgres_commit_por_mensaje   autocommit, WAL a disco en cada mensaje
        postgres_commit_asincrono     synchronous_commit = off
        postgres_lote                 una transacción cada --lote mensajes
        valkey_por_mensaje            una llamada al script por mensaje
        valkey_aof_always             igual, con bitácora AOF a disco en cada escritura
        valkey_pipeline               --lote llamadas por viaje de red

    Al final se verifica que las seis den los mismos conteos y alertas.

Usted escribe:
    TODO 4 — lua/feed.lua: la lógica del mensaje en el servidor
    TODO 5 — enviar_en_lotes(): la variante postgres_lote
"""

from __future__ import annotations

import argparse
import random
import statistics

from common import (
    CSV_COLUMNS, LAB, Timer, check, iter_rows, pg_connect, record, valkey_connect,
)

I_VENDOR = CSV_COLUMNS.index("vendor_id")
I_PAY = CSV_COLUMNS.index("payment_type")
I_FARE = CSV_COLUMNS.index("fare_amount")
I_DIST = CSV_COLUMNS.index("trip_distance")

INSERT = (
    "INSERT INTO feed_trip (vendor_id, payment_type, fare_amount, trip_distance)"
    " VALUES (%s, %s, %s, %s)"
)

# Las cuatro llaves que escribe lua/feed.lua.
FEED_KEYS = ("agg:n", "agg:suma", "alarma:anomalias", "alarma:alertas")

# Un mensaje es (vendor_id, payment_type, fare_amount, trip_distance, anomalia).
Message = tuple[str, str, str, str, int]


# ---------------------------------------------------------------- 3a

def p50_ms(fn, ids) -> float:
    """Mediana de la latencia de fn(id) sobre todos los ids, en ms."""
    lat = []
    for i in ids:
        with Timer() as t:
            fn(i)
        lat.append(t.s * 1000)
    return statistics.median(lat)


def operaciones_por_llave(ops: int, seed: int) -> None:
    r = valkey_connect()
    vk_rows = r.dbsize() - sum(r.exists(k) for k in FEED_KEYS)
    if vk_rows <= 0:
        raise SystemExit("Valkey no tiene viajes. Corra cargar.py.")
    # Mismos ids para los dos motores, y la semilla fija los hace repetibles.
    ids = random.Random(seed).sample(range(1, vk_rows + 1), ops)

    with pg_connect() as conn, conn.cursor() as cur:
        def pg_read(i):
            cur.execute("SELECT * FROM trips WHERE trip_id = %s", (i,))
            cur.fetchone()

        def pg_update(i):
            cur.execute("UPDATE trips SET tip_amount = tip_amount + 1 WHERE trip_id = %s", (i,))

        record("3a-puntual", "postgres", "lectura_por_llave_p50", p50_ms(pg_read, ids), "ms")
        record("3a-puntual", "postgres", "update_por_llave_p50", p50_ms(pg_update, ids), "ms")

    record("3a-puntual", "valkey", "lectura_por_llave_p50",
           p50_ms(lambda i: r.hgetall(f"trip:{i}"), ids), "ms")
    record("3a-puntual", "valkey", "update_por_llave_p50",
           p50_ms(lambda i: r.hincrbyfloat(f"trip:{i}", "tip_amount", 1), ids), "ms")


# ---------------------------------------------------------------- 3b

def mensajes(n: int) -> list[Message]:
    """Los primeros n viajes del CSV, convertidos en mensajes del feed.
    Se leen una sola vez y todas las variantes reciben la misma lista."""
    out = []
    for row in iter_rows(n):
        fare, dist = float(row[I_FARE]), float(row[I_DIST])
        anom = 1 if dist <= 0 or fare <= 0 else 0
        out.append((row[I_VENDOR], row[I_PAY], row[I_FARE], row[I_DIST], anom))
    return out


def enviar_uno_por_uno(conn, msgs: list[Message]) -> None:
    """Con autocommit, cada INSERT es una transacción: un commit por mensaje."""
    with conn.cursor() as cur:
        for m in msgs:
            cur.execute(INSERT, m[:4])


def enviar_en_lotes(conn, msgs: list[Message], batch: int) -> None:
    """Variante postgres_lote: una transacción cada `batch` mensajes.

    La conexión está en autocommit. `with conn.transaction():` abre una
    transacción explícita que se confirma al salir del bloque, así que todos los
    INSERT de adentro comparten un solo commit (y una sola espera del WAL).
    cursor.executemany(INSERT, filas) envía muchas filas con la misma sentencia.
    El trigger se sigue disparando por cada fila: la lógica no cambia, solo
    cuántas veces se espera al disco.
    """
    # TODO 5 (paso 3b)
    #   a) Recorra msgs en tramos de `batch`: range(0, len(msgs), batch).
    #   b) Por tramo, abra `with conn.transaction(), conn.cursor() as cur:`.
    #   c) Adentro, cur.executemany(INSERT, filas), donde filas son los primeros
    #      cuatro campos de cada mensaje del tramo (m[:4]); el quinto, la anomalía,
    #      lo calcula el trigger por su cuenta.
    # Verificación automática: postgres_lote da la misma respuesta que las demás.
    # Compare enviar_uno_por_uno(): la única diferencia es dónde termina la transacción.
    raise NotImplementedError("TODO 5: enviar_en_lotes()")


def feed_postgres(msgs: list[Message], variant: str, batch: int, umbral: int) -> dict:
    ddl = (LAB / "sql" / "pg_feed.sql").read_text()
    with pg_connect() as conn:
        conn.execute(ddl)  # tablas vacías y trigger nuevo en cada variante
        conn.execute(f"SET lab2.umbral = {int(umbral)}")
        if variant == "commit_asincrono":
            # El commit responde sin esperar a que el WAL llegue a disco.
            # Si el servidor cae, se pierde la última fracción de segundo.
            conn.execute("SET synchronous_commit = off")
        with Timer() as t:
            if variant == "lote":
                enviar_en_lotes(conn, msgs, batch)
            else:
                enviar_uno_por_uno(conn, msgs)
        rate = len(msgs) / t.s
        with Timer() as tq:
            rows = conn.execute("SELECT payment_type, n, suma FROM agg_pago").fetchall()
        alerts = conn.execute("SELECT COALESCE(sum(alertas), 0) FROM alarma_vendor").fetchone()[0]
    record("3b-feed", f"postgres_{variant}", "mensajes_por_s", rate, "msg/s", mensajes=len(msgs))
    record("3b-feed", f"postgres_{variant}", "leer_respuesta", tq.s * 1000, "ms")
    return {"conteos": {str(pt): n for pt, n, _ in rows}, "alertas": int(alerts)}


def feed_valkey(msgs: list[Message], variant: str, batch: int, umbral: int) -> dict:
    r = valkey_connect()
    r.delete(*FEED_KEYS)
    # register_script sube el Lua una vez y después lo llama por su hash (EVALSHA).
    # Todo el script corre dentro del servidor, sin volver al cliente.
    script = r.register_script((LAB / "lua" / "feed.lua").read_text())
    if variant == "aof_always":
        # AOF = append-only file: Valkey anota cada escritura en una bitácora.
        # appendfsync always la fuerza a disco antes de responder, como el WAL
        # de Postgres con synchronous_commit = on.
        r.config_set("appendonly", "yes")
        r.config_set("appendfsync", "always")
    try:
        with Timer() as t:
            if variant == "pipeline":
                # Mismo script, pero `batch` llamadas viajan juntas y las
                # respuestas vuelven juntas: un viaje de red por lote.
                for i in range(0, len(msgs), batch):
                    pipe = r.pipeline(transaction=False)
                    for v, pt, fare, _dist, anom in msgs[i:i + batch]:
                        script(args=[pt, fare, v, anom, umbral], client=pipe)
                    pipe.execute()
            else:
                for v, pt, fare, _dist, anom in msgs:
                    script(args=[pt, fare, v, anom, umbral])
    finally:
        if variant == "aof_always":
            r.config_set("appendonly", "no")
    rate = len(msgs) / t.s
    with Timer() as tq:
        counts = r.hgetall("agg:n")
        r.hgetall("agg:suma")
    alerts = sum(int(x) for x in r.hgetall("alarma:alertas").values())
    record("3b-feed", f"valkey_{variant}", "mensajes_por_s", rate, "msg/s", mensajes=len(msgs))
    record("3b-feed", f"valkey_{variant}", "leer_respuesta", tq.s * 1000, "ms")
    return {"conteos": {k: int(v) for k, v in counts.items()}, "alertas": alerts}


def respuesta_esperada(msgs: list[Message], umbral: int) -> dict:
    """Lo que las seis variantes deben dar, calculado en Python puro."""
    counts: dict[str, int] = {}
    anomalias: dict[str, int] = {}
    alerts = 0
    for v, pt, _fare, _dist, anom in msgs:
        counts[pt] = counts.get(pt, 0) + 1
        if anom:
            anomalias[v] = anomalias.get(v, 0) + 1
            if anomalias[v] % umbral == 0:
                alerts += 1
    return {"conteos": counts, "alertas": alerts}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--operaciones", type=int, default=2_000)
    ap.add_argument("--mensajes", type=int, default=10_000)
    ap.add_argument("--lote", type=int, default=1_000)
    ap.add_argument("--semilla", type=int, default=4601)
    ap.add_argument("--umbral", type=int, default=10, help="anomalías por alerta (el paper usa 100)")
    ap.add_argument("--solo-feed", action="store_true", help="omite 3a")
    args = ap.parse_args()

    if not args.solo_feed:
        print(f"3a: {args.operaciones} lecturas y updates por llave")
        operaciones_por_llave(args.operaciones, args.semilla)

    print(f"3b: feed de {args.mensajes:,} mensajes")
    msgs = mensajes(args.mensajes)
    expected = respuesta_esperada(msgs, args.umbral)
    print(f"  esperado: {expected['alertas']} alertas, conteos {dict(sorted(expected['conteos'].items()))}")

    for variant in ("commit_por_mensaje", "commit_asincrono", "lote"):
        got = feed_postgres(msgs, variant, args.lote, args.umbral)
        check(got == expected, f"postgres_{variant} da la respuesta esperada"
              + (" (TODO 5)" if variant == "lote" else ""))
    for variant in ("por_mensaje", "aof_always", "pipeline"):
        got = feed_valkey(msgs, variant, args.lote, args.umbral)
        check(got == expected, f"valkey_{variant} da la respuesta esperada (TODO 4)")


if __name__ == "__main__":
    main()
