#!/usr/bin/env python3
"""Sonda de escrituras para medir disponibilidad durante una falla de nodo."""

from __future__ import annotations

import argparse
import csv
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def connect() -> psycopg.Connection:
    return psycopg.connect(
        connect_timeout=2,
        options="-c statement_timeout=2000",
        autocommit=True,
    )


def write_once() -> None:
    with connect() as conn:
        updated = conn.execute(
            """
            UPDATE ti4601_raft.public.raft_probe
            SET version = version + 1, updated_at = now()
            WHERE id = 1
            RETURNING version
            """
        ).fetchone()
        if updated is None:
            raise RuntimeError(
                "No existe raft_probe; aplique raft_probe.sql según el README"
            )


def read_signal(path: Path) -> float | None:
    try:
        return float(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--label", default="Chaos A")
    parser.add_argument(
        "--signal-file",
        default="evidence/chaos-a-stop.epoch",
        help="Archivo que el host crea inmediatamente después de docker stop",
    )
    parser.add_argument("--csv", default="evidence/chaos-a.csv")
    args = parser.parse_args()

    signal_path = Path(args.signal_file)
    output_path = Path(args.csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    started = time.time()
    samples: list[dict[str, str]] = []
    first_ok_after_signal: float | None = None
    failures_after_signal = 0

    print(f"=== Lab 1 · sonda {args.label} ===")
    print(f"PGHOST={os.environ.get('PGHOST')}")
    print("Fila objetivo: ti4601_raft.public.raft_probe(id=1), RF=3")
    print(f"Señal de falla: {signal_path}")

    while time.time() - started < args.duration:
        attempt_started = time.time()
        perf_started = time.perf_counter_ns()
        status = "ok"
        error = ""
        try:
            write_once()
        except Exception as exc:  # La clase concreta cambia por causa/host.
            status = "error"
            error = f"{type(exc).__name__}: {str(exc).splitlines()[0]}"[:240]
        latency_ms = (time.perf_counter_ns() - perf_started) / 1_000_000
        completed_at = time.time()

        signal_at = read_signal(signal_path)
        phase = "before-stop"
        if signal_at is not None and completed_at >= signal_at:
            phase = "after-stop"
            if status == "error":
                failures_after_signal += 1
            elif first_ok_after_signal is None:
                first_ok_after_signal = completed_at

        sample = {
            "timestamp_utc": utc_now(),
            "epoch": f"{attempt_started:.6f}",
            "completed_epoch": f"{completed_at:.6f}",
            "phase": phase,
            "status": status,
            "latency_ms": f"{latency_ms:.3f}",
            "error": error,
        }
        samples.append(sample)
        print(
            f"{sample['timestamp_utc']} {phase:11} {status:5} "
            f"{latency_ms:8.3f} ms {error}"
        )
        time.sleep(max(0.0, args.interval - (time.time() - attempt_started)))

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=samples[0].keys())
        writer.writeheader()
        writer.writerows(samples)

    signal_at = read_signal(signal_path)
    print(f"\nMuestras: {output_path}")
    print(f"Errores después de la señal: {failures_after_signal}")
    if signal_at is None:
        print("RTO no calculado: nunca apareció el archivo de señal.")
    elif first_ok_after_signal is None:
        print("RTO no observado: no hubo escritura OK después de la señal.")
    else:
        rto_ms = max(0.0, (first_ok_after_signal - signal_at) * 1000)
        print(f"RTO observado hasta primer write OK: {rto_ms:.1f} ms")
    print(
        "RPO se verifica después: la fila committed anterior debe seguir "
        "presente y su version no debe retroceder."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

