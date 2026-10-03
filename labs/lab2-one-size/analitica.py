#!/usr/bin/env python3
"""Paso 2 — La consulta de almacén en los dos motores.

    SELECT payment_type, AVG(fare_amount), COUNT(*) FROM trips GROUP BY payment_type

Postgres
    Tiene la primitiva: el optimizador elige un plan (escaneo secuencial en
    paralelo + agregación por hash) y lo ejecuta dentro del servidor. Se guarda
    el plan de EXPLAIN (ANALYZE, BUFFERS) y se mide la mediana de cinco corridas,
    sobre la tabla completa y sobre el mismo subconjunto que tiene Valkey.

Valkey
    No tiene GROUP BY. Un almacén clave-valor solo sabe «dame el valor de esta
    llave». Para agregar, el cliente tiene que recorrer todas las llaves (SCAN),
    traer los dos campos que necesita de cada una (HMGET) y sumar él mismo.
    Eso es exactamente lo que el paper llama no tener las primitivas correctas
    solo que al revés: aquí el especialista es el que no las tiene.

Al final, Postgres responde una pregunta que nadie previó al diseñar el lab
(propina promedio por hora del día). Valkey no puede sin cargar otro modelo.

Usted escribe:
    TODO 3 — agregar_lote(): el GROUP BY hecho a mano en el cliente
"""

from __future__ import annotations

import argparse
import re
import statistics

from common import EVIDENCE, LAB, Timer, check, pg_connect, record, valkey_connect

# sql/olap.sql sin su línea de comentario inicial ni el punto y coma final.
OLAP = (LAB / "sql" / "olap.sql").read_text().split(";")[0].split("\n", 1)[1]

ADHOC = """
SELECT extract(hour FROM pickup_at) AS hora, AVG(tip_amount) AS propina
FROM trips WHERE payment_type = 1 GROUP BY 1 ORDER BY 1
"""

SCAN_BATCH = 10_000


def execution_ms(plan: str) -> float:
    """Extrae 'Execution Time: X ms' del texto de EXPLAIN ANALYZE."""
    return float(re.search(r"Execution Time: ([\d.]+) ms", plan).group(1))


def mediana_ms(cur, sql: str, runs: int) -> tuple[float, list]:
    """Corre `sql` varias veces y devuelve la mediana en ms y el último resultado.
    La primera corrida suele ser más lenta (páginas que aún no están en caché);
    la mediana no se deja arrastrar por ella."""
    times, rows = [], []
    for _ in range(runs):
        with Timer() as t:
            cur.execute(sql)
            rows = cur.fetchall()
        times.append(t.s * 1000)
    return statistics.median(times), rows


def postgres(runs: int, subset: int) -> dict[str, tuple[float, int]]:
    with pg_connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM trips")
        total = cur.fetchone()[0]

        # EXPLAIN ANALYZE ejecuta la consulta de verdad y anota, en cada nodo del
        # plan, filas reales y tiempo. BUFFERS agrega cuántas páginas de 8 KiB
        # salieron de la caché (hit) y cuántas se leyeron (read).
        cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + OLAP)
        plan = "\n".join(r[0] for r in cur.fetchall())
        (EVIDENCE / "plan_olap_postgres.txt").write_text(plan + "\n")
        print(plan)
        record("2-olap", "postgres", "explain_execution_time", execution_ms(plan), "ms", filas=total)

        ms, rows = mediana_ms(cur, OLAP, runs)
        record("2-olap", "postgres", "mediana_completa", ms, "ms", filas=total)
        (EVIDENCE / "respuesta_olap_postgres.txt").write_text(
            "\n".join(f"{pt}\t{avg:.4f}\t{n}" for pt, avg, n in rows) + "\n"
        )

        # Mismas filas que tiene Valkey: trip_id 1..subset.
        sub = OLAP.replace("FROM trips", f"FROM trips WHERE trip_id <= {subset}")
        ms, sub_rows = mediana_ms(cur, sub, runs)
        record("2-olap", "postgres", "mediana_subconjunto", ms, "ms", filas=subset)

        with Timer() as t:
            cur.execute(ADHOC)
            cur.fetchall()
        record("2-olap", "postgres", "pregunta_nueva", t.s * 1000, "ms", filas=total)
    return {str(pt): (float(avg), n) for pt, avg, n in sub_rows}


def agregar_lote(r, keys: list[str], sums: dict[str, float], counts: dict[str, int]) -> None:
    """Agrega un lote de llaves trip:* a los acumuladores `sums` y `counts`.

    Para cada llave hay que leer dos campos del hash: payment_type y fare_amount.
    Al final de todos los lotes debe cumplirse, para cada tipo de pago pt:

        counts[pt] == número de viajes con ese payment_type
        sums[pt]   == suma de fare_amount de esos viajes

    Los valores llegan como str (Valkey no tiene tipos). Use un pipeline para no
    pagar un viaje de red por llave: HMGET por cada llave, un solo execute().
    """
    # TODO 3 (paso 2)
    #   a) pipe = r.pipeline(transaction=False)
    #   b) Por cada llave k, encole pipe.hmget(k, "payment_type", "fare_amount").
    #   c) pipe.execute() devuelve una lista con una respuesta por comando, en el
    #      mismo orden: cada respuesta es [payment_type, fare_amount], ambos str.
    #   d) Acumule en los diccionarios que recibe (no cree otros): sume float(fare)
    #      en sums[pt] y 1 en counts[pt]. dict.get(pt, 0) evita el KeyError.
    # Verificación automática: mismos conteos y promedios que Postgres sobre las
    # mismas filas. Usted acaba de escribir el HashAggregate del plan de Postgres.
    raise NotImplementedError("TODO 3: agregar_lote()")


def valkey() -> tuple[int, dict[str, tuple[float, int]]]:
    r = valkey_connect()
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    n = 0
    with Timer() as t:
        # SCAN recorre el espacio de llaves por tandas sin bloquear al servidor
        # (KEYS * lo bloquearía). `count` es una sugerencia de tamaño de tanda.
        batch: list[str] = []
        for key in r.scan_iter(match="trip:*", count=SCAN_BATCH):
            batch.append(key)
            if len(batch) == SCAN_BATCH:
                agregar_lote(r, batch, sums, counts)
                n += len(batch)
                batch = []
        if batch:
            agregar_lote(r, batch, sums, counts)
            n += len(batch)
    if n == 0:
        raise SystemExit("Valkey no tiene viajes. Corra cargar.py.")
    record("2-olap", "valkey", "agregado_en_cliente", t.s * 1000, "ms", filas=n)
    answer = {pt: (sums[pt] / counts[pt], counts[pt]) for pt in counts}
    (EVIDENCE / "respuesta_olap_valkey.txt").write_text(
        "\n".join(f"{pt}\t{avg:.4f}\t{c}" for pt, (avg, c) in sorted(answer.items())) + "\n"
    )
    return n, answer


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corridas", type=int, default=5)
    args = ap.parse_args()
    EVIDENCE.mkdir(exist_ok=True)

    print("Valkey: SCAN + HMGET, agregado en el cliente")
    n, vk = valkey()
    print("Postgres: EXPLAIN ANALYZE y corridas")
    pg = postgres(args.corridas, n)

    # Las dos respuestas sobre las mismas filas tienen que coincidir.
    same_counts = {pt: c for pt, (_, c) in vk.items()} == {pt: c for pt, (_, c) in pg.items()}
    same_avgs = all(abs(vk[pt][0] - pg[pt][0]) < 1e-6 for pt in pg if pt in vk)
    check(same_counts and same_avgs,
          "TODO 3: el GROUP BY a mano da los mismos conteos y promedios que Postgres")


if __name__ == "__main__":
    main()
