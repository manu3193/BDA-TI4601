"""Utilidades compartidas por todos los scripts del Laboratorio 2.

Aquí no hay mediciones. Hay cuatro cosas que todos los pasos necesitan:

1. Leer el CSV de Kaggle directamente desde el zip, sin descomprimirlo a disco.
2. Abrir una conexión a cada motor (Postgres por psycopg, Valkey por redis-py).
3. Registrar cada medida en evidence/resultados.jsonl, una línea JSON por medida,
   para que graficas.py pueda dibujar todo al final.
4. Un cronómetro (Timer) basado en time.perf_counter(), que es el reloj
   monotónico de mayor resolución que ofrece Python.
"""

from __future__ import annotations

import csv
import io
import json
import os
import time
import zipfile
from pathlib import Path
from typing import Iterator

LAB = Path(__file__).resolve().parent
DATA = LAB / "data"
EVIDENCE = LAB / "evidence"
RESULTS = EVIDENCE / "resultados.jsonl"

KAGGLE_DATASET = "elemento/nyc-yellow-taxi-trip-data"
CSV_NAME = "yellow_tripdata_2016-01.csv"
ZIP_PATH = DATA / f"{CSV_NAME}.zip"
FULL_MONTH_ROWS = 10_906_858

# Nombres de columna en el orden exacto del encabezado del CSV 2016-01.
# Los usamos en snake_case para Postgres (sql/pg_trips.sql) y como nombres
# de campo de cada hash en Valkey. Así las dos copias del dato son comparables.
CSV_COLUMNS = [
    "vendor_id", "pickup_at", "dropoff_at", "passenger_count", "trip_distance",
    "pickup_longitude", "pickup_latitude", "ratecode_id", "store_and_fwd_flag",
    "dropoff_longitude", "dropoff_latitude", "payment_type", "fare_amount",
    "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge",
    "total_amount",
]

# None significa «todo el archivo».
PROFILES = {"completo": None, "reducido": 2_000_000}


def data_source() -> Path:
    """Devuelve el zip de Kaggle o, si el estudiante ya lo descomprimió, el CSV."""
    csv_path = DATA / CSV_NAME
    if csv_path.exists():
        return csv_path
    if ZIP_PATH.exists():
        return ZIP_PATH
    raise SystemExit(
        f"No encuentro {ZIP_PATH} ni {csv_path}. Corra primero descargar.py."
    )


def open_csv_text() -> io.TextIOBase:
    """Abre el CSV como texto. Si está dentro del zip, se descomprime en streaming:
    Python lee y descomprime por bloques, sin escribir los 1,7 GB a disco."""
    src = data_source()
    if src.suffix == ".zip":
        zf = zipfile.ZipFile(src)
        return io.TextIOWrapper(zf.open(CSV_NAME), encoding="utf-8", newline="")
    return open(src, encoding="utf-8", newline="")


def iter_lines(limit: int | None) -> Iterator[str]:
    """Líneas crudas del CSV, sin el encabezado, en el orden del archivo.

    Es un generador: produce una línea a la vez y nunca tiene el archivo entero
    en memoria. `limit` corta después de esa cantidad de filas."""
    with open_csv_text() as fh:
        fh.readline()  # encabezado
        for i, line in enumerate(fh):
            if limit is not None and i >= limit:
                break
            yield line


def iter_rows(limit: int | None) -> Iterator[list[str]]:
    """Igual que iter_lines, pero cada fila ya separada en una lista de strings."""
    yield from csv.reader(iter_lines(limit))


def row_limit(profile: str, rows: int | None) -> int | None:
    """Un --filas explícito gana sobre el perfil."""
    if rows is not None:
        return rows
    return PROFILES[profile]


def pg_connect(autocommit: bool = True):
    """Conexión a Postgres. Host, usuario y clave vienen de las variables PG* que
    docker-compose.yml le pone al contenedor app.

    autocommit=True: cada sentencia es su propia transacción y se confirma sola.
    Es lo que hace una aplicación OLTP típica, y es lo que queremos medir en el
    paso 3 cuando hablamos de «un commit por mensaje»."""
    import psycopg

    return psycopg.connect(autocommit=autocommit)


def valkey_connect():
    """Conexión a Valkey. redis-py habla el mismo protocolo (RESP), así que sirve
    sin cambios. decode_responses=True devuelve str en vez de bytes."""
    import redis

    return redis.Redis(
        host=os.environ.get("VALKEY_HOST", "valkey"),
        port=int(os.environ.get("VALKEY_PORT", "6379")),
        decode_responses=True,
    )


def record(step: str, engine: str, metric: str, value: float, unit: str, **extra) -> None:
    """Agrega una medida a evidence/resultados.jsonl y la imprime.

    Nunca se sobrescribe: si repite un paso, queda la historia completa y
    graficas.py usa la última medida de cada (paso, motor, métrica)."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "paso": step,
        "motor": engine,
        "metrica": metric,
        "valor": round(value, 6),
        "unidad": unit,
        **extra,
    }
    with RESULTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"  [{step}] {engine:<28} {metric:<26} {value:>14,.3f} {unit}")


class Timer:
    """Cronómetro de pared para usar con `with`.

        with Timer() as t:
            hacer_algo()
        print(t.s)   # segundos transcurridos
    """

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.s = time.perf_counter() - self.t0


def check(ok: bool, what: str) -> None:
    """Verificación automática de los TODO. Si falla, el script se detiene:
    una medida sobre código incorrecto no sirve para el reporte."""
    if not ok:
        raise SystemExit(f"VERIFICACIÓN FALLÓ: {what}")
    print(f"  OK: {what}")
