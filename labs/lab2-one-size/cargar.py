#!/usr/bin/env python3
"""Paso 1 — Cargar el mismo CSV en los dos motores y medir cuánto espacio ocupa.

Postgres (row-store en disco)
    La tabla se crea con sql/pg_trips.sql y se llena con COPY, el mecanismo de
    carga masiva de Postgres: el cliente manda el CSV como un flujo de bytes y el
    servidor lo parsea, sin una sentencia INSERT por fila. Luego se construye la
    llave primaria (un índice B-tree) y se miden heap e índices.

Valkey (clave-valor en RAM)
    Cada viaje se guarda como un hash: la llave es `trip:<id>` y los campos son
    las 19 columnas del CSV. Todo vive en memoria. Por defecto se cargan solo
    1 000 000 de viajes y el costo por viaje se extrapola al mes completo.

Usted escribe:
    TODO 1 — medir_espacio_postgres()
    TODO 2 — cargar_valkey(): el envío por lotes con pipeline
"""

from __future__ import annotations

import argparse

from common import (
    CSV_COLUMNS, FULL_MONTH_ROWS, LAB, Timer, check, iter_lines, iter_rows,
    pg_connect, record, row_limit, valkey_connect,
)

COPY_SQL = f"COPY trips ({', '.join(CSV_COLUMNS)}) FROM STDIN WITH (FORMAT csv)"

# COPY recibe el CSV en bloques de ~8 MiB. Mandar línea por línea también
# funciona, pero cada write() tiene su costo en Python.
COPY_CHUNK_BYTES = 8 << 20

# Cuántos HSET se acumulan en el pipeline antes de enviarlos a Valkey.
PIPELINE_BATCH = 10_000


def medir_espacio_postgres(cur) -> tuple[int, int, int]:
    """Devuelve (bytes_heap, bytes_indices, bytes_total) de la tabla trips.

    Postgres guarda cada tabla en un archivo «heap» con páginas de 8 KiB y cada
    índice en archivos aparte. El catálogo expone funciones para medirlos:

        pg_relation_size('trips')        solo el heap (las filas)
        pg_indexes_size('trips')         todos los índices de la tabla
        pg_total_relation_size('trips')  heap + índices + TOAST

    `cur` es un cursor de psycopg ya abierto.
    """
    # TODO 1 (paso 1)
    #   a) Ejecute con cur.execute(...) UNA sentencia SELECT que devuelva las tres
    #      funciones de arriba en ese orden.
    #   b) Lea la única fila con cur.fetchone(); es una tupla de tres enteros.
    #   c) Devuélvala tal cual. Las unidades son bytes; cargar_postgres() la pasa a MiB.
    # Verificación automática: total >= heap + índices, y ambos > 0.
    raise NotImplementedError("TODO 1: medir_espacio_postgres()")


def cargar_postgres(limit: int | None) -> int:
    ddl = (LAB / "sql" / "pg_trips.sql").read_text()
    with pg_connect() as conn, conn.cursor() as cur:
        cur.execute(ddl)

        n = 0
        buf: list[str] = []
        size = 0
        with Timer() as t_copy:
            with cur.copy(COPY_SQL) as cp:
                for line in iter_lines(limit):
                    buf.append(line)
                    size += len(line)
                    n += 1
                    if size >= COPY_CHUNK_BYTES:
                        cp.write("".join(buf))
                        buf, size = [], 0
                if buf:
                    cp.write("".join(buf))
        record("1-carga", "postgres", "filas", n, "filas")
        record("1-carga", "postgres", "tiempo_copy", t_copy.s, "s")
        record("1-carga", "postgres", "filas_por_s", n / t_copy.s, "filas/s")

        # El índice se construye después de cargar: ordenar una vez 10 M llaves
        # es mucho más barato que mantener el B-tree fila por fila durante COPY.
        with Timer() as t_pk:
            cur.execute("ALTER TABLE trips ADD PRIMARY KEY (trip_id)")
        record("1-carga", "postgres", "tiempo_indice_pk", t_pk.s, "s")

        # VACUUM ANALYZE actualiza las estadísticas que usa el optimizador
        # en el paso 2 y deja el mapa de visibilidad al día.
        cur.execute("VACUUM (ANALYZE) trips")

        heap, idx, total = medir_espacio_postgres(cur)
        check(heap > 0 and idx > 0 and total >= heap + idx,
              "TODO 1: total >= heap + índices, y ambos > 0")
        record("1-carga", "postgres", "disco_tabla", heap / 2**20, "MiB")
        record("1-carga", "postgres", "disco_indices", idx / 2**20, "MiB")
        record("1-carga", "postgres", "disco_total", total / 2**20, "MiB")
        record("1-carga", "postgres", "bytes_por_fila", total / n, "B/fila")
    return n


def cargar_valkey(r, limit: int) -> int:
    """Guarda los primeros `limit` viajes como hashes y devuelve cuántos guardó.

    El viaje número k (empezando en 1) va en la llave f"trip:{k}", con un campo
    por columna: dict(zip(CSV_COLUMNS, row)). Es el mismo número que Postgres
    le asigna en trip_id, porque ambos leen el CSV en el mismo orden.

    Un HSET por viaje, enviado de a uno, obliga a esperar la respuesta de la red
    un millón de veces. Un pipeline acumula comandos en el cliente y los manda
    juntos: un viaje de ida y vuelta por lote en vez de uno por comando.
    """
    # TODO 2 (paso 1)
    #   a) Cree un pipeline sin transacción: r.pipeline(transaction=False).
    #      (transaction=True lo envolvería en MULTI/EXEC; aquí no lo necesitamos.)
    #   b) Recorra iter_rows(limit) numerando desde 1: enumerate(..., start=1).
    #   c) Por cada fila, encole pipe.hset(llave, mapping=...). Encolar no envía nada.
    #   d) Cada PIPELINE_BATCH filas, llame pipe.execute(): ahí viaja el lote.
    #   e) Al salir del ciclo, un último pipe.execute() para el lote incompleto.
    #   f) Devuelva cuántas filas guardó.
    # Verificación automática: dbsize() == limit y el último viaje tiene fare_amount.
    # Para pensar: ¿qué pasaría con el tiempo de carga si llamara r.hset() directo?
    raise NotImplementedError("TODO 2: cargar_valkey()")


def medir_valkey(limit: int, pg_rows: int) -> None:
    r = valkey_connect()
    r.flushall()
    base = r.info("memory")["used_memory"]
    with Timer() as t:
        n = cargar_valkey(r, limit)
    check(r.dbsize() == n == limit, f"TODO 2: Valkey tiene {limit:,} llaves trip:*")
    check(r.hget(f"trip:{n}", "fare_amount") is not None,
          "TODO 2: el último viaje tiene el campo fare_amount")

    # used_memory es la memoria que Valkey reporta para sus datos. Restamos la
    # base para quedarnos con lo que ocupan los viajes.
    used = r.info("memory")["used_memory"] - base
    record("1-carga", "valkey", "filas", n, "filas")
    record("1-carga", "valkey", "tiempo_carga", t.s, "s")
    record("1-carga", "valkey", "filas_por_s", n / t.s, "filas/s")
    record("1-carga", "valkey", "ram_usada", used / 2**20, "MiB")
    record("1-carga", "valkey", "bytes_por_fila", used / n, "B/fila")
    record(
        "1-carga", "valkey", "ram_extrapolada_total", used / n * pg_rows / 2**20, "MiB",
        nota=f"extrapolado a {pg_rows} filas",
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perfil", choices=["completo", "reducido"], default="completo")
    ap.add_argument("--filas", type=int, help="límite explícito para Postgres")
    ap.add_argument("--filas-valkey", type=int, default=1_000_000)
    ap.add_argument("--solo", choices=["postgres", "valkey"])
    args = ap.parse_args()

    limit = row_limit(args.perfil, args.filas)
    pg_rows = limit or FULL_MONTH_ROWS
    if args.solo != "valkey":
        print(f"Postgres: COPY de {'todo el archivo' if limit is None else f'{limit:,} filas'}")
        pg_rows = cargar_postgres(limit)
    if args.solo != "postgres":
        vk = min(args.filas_valkey, pg_rows)
        print(f"Valkey: HSET de {vk:,} filas")
        medir_valkey(vk, pg_rows)


if __name__ == "__main__":
    main()
