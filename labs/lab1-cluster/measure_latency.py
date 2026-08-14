#!/usr/bin/env python3
"""Mide latencia de commits UPSERT contra el motor (Lab 1).

Uso:
  docker compose --profile lab1 run --rm app-crdb \\
    python3 labs/lab1-cluster/measure_latency.py
"""

from __future__ import annotations

import statistics
import time

import psycopg

N = 30


def main() -> None:
    samples_ms: list[float] = []
    with psycopg.connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ping (
                      id INT PRIMARY KEY,
                      note STRING,
                      region STRING NOT NULL DEFAULT 'r1',
                      written_at TIMESTAMPTZ DEFAULT now()
                    )
                    """
                )
        for i in range(N):
            t0 = time.perf_counter()
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        "UPSERT INTO ping (id, note) VALUES (1, %s)",
                        (f"lat-{i}",),
                    )
            samples_ms.append((time.perf_counter() - t0) * 1000.0)

    samples_ms.sort()
    p50 = statistics.median(samples_ms)
    p90 = samples_ms[int(0.9 * (len(samples_ms) - 1))]
    print(f"n={N}")
    print(f"p50_ms={p50:.2f}")
    print(f"p90_ms={p90:.2f}")
    print(f"min_ms={samples_ms[0]:.2f}")
    print(f"max_ms={samples_ms[-1]:.2f}")


if __name__ == "__main__":
    main()
