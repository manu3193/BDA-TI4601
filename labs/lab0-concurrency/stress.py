#!/usr/bin/env python3
"""
Laboratorio de concurrencia — Lost Update vs SERIALIZABLE + reintentos.

  make lab-concurrency ISOLATION=READ_COMMITTED
  make lab-concurrency ISOLATION=SERIALIZABLE
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import threading
import time
from dataclasses import dataclass, field

import psycopg
from psycopg import IsolationLevel, errors


ACCOUNT_ID = 1
INITIAL = 1000

_ISO = {
    "READ_COMMITTED": IsolationLevel.READ_COMMITTED,
    "SERIALIZABLE": IsolationLevel.SERIALIZABLE,
}


@dataclass
class Stats:
    ok: int = 0
    serialization_failures: int = 0
    other_errors: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def inc_ok(self) -> None:
        with self.lock:
            self.ok += 1

    def inc_ser(self) -> None:
        with self.lock:
            self.serialization_failures += 1

    def inc_other(self) -> None:
        with self.lock:
            self.other_errors += 1


def connect() -> psycopg.Connection:
    # libpq: PGHOST/PGPORT/… inyectadas por Compose (solo Postgres en este lab).
    return psycopg.connect(autocommit=False)


def reset_account() -> None:
    with connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE accounts SET balance = %s WHERE id = %s",
                    (INITIAL, ACCOUNT_ID),
                )


def read_balance() -> float:
    with connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT balance::float FROM accounts WHERE id = %s",
                    (ACCOUNT_ID,),
                )
                row = cur.fetchone()
                return float(row[0])


def debit_once(isolation: IsolationLevel, stats: Stats, max_retries: int) -> None:
    """Lee balance, espera, escribe balance-1 (anti-patrón de lost update)."""
    attempt = 0
    while True:
        attempt += 1
        try:
            with connect() as conn:
                conn.isolation_level = isolation
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT balance FROM accounts WHERE id = %s",
                            (ACCOUNT_ID,),
                        )
                        balance = cur.fetchone()[0]
                        time.sleep(0.002)
                        cur.execute(
                            "UPDATE accounts SET balance = %s WHERE id = %s",
                            (balance - 1, ACCOUNT_ID),
                        )
            stats.inc_ok()
            return
        except errors.SerializationFailure:
            stats.inc_ser()
            if attempt >= max_retries:
                return
            delay = (2 ** (attempt - 1)) * 0.005 + random.uniform(0, 0.005)
            time.sleep(delay)
        except Exception:
            stats.inc_other()
            return


def run_burst(isolation: IsolationLevel, workers: int, retries: int) -> Stats:
    reset_account()
    stats = Stats()
    threads = [
        threading.Thread(target=debit_once, args=(isolation, stats, retries))
        for _ in range(workers)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return stats


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--isolation",
        choices=tuple(_ISO.keys()),
        default=os.environ.get("ISOLATION", "READ_COMMITTED"),
    )
    p.add_argument("--workers", type=int, default=int(os.environ.get("WORKERS", "40")))
    p.add_argument("--retries", type=int, default=int(os.environ.get("RETRIES", "8")))
    args = p.parse_args()

    isolation = _ISO[args.isolation]
    print(f"=== Lab concurrencia · {args.isolation} · workers={args.workers} ===")
    print(f"Saldo inicial: {INITIAL}")

    stats = run_burst(isolation, args.workers, args.retries)
    final = read_balance()
    expected_if_atomic = float(INITIAL - stats.ok)

    print(f"Commits OK:              {stats.ok}")
    print(f"SerializationFailure:    {stats.serialization_failures}")
    print(f"Otros errores:           {stats.other_errors}")
    print(f"Saldo final observado:   {final}")
    print(f"Esperado si cada OK −1:  {expected_if_atomic}")

    if args.isolation == "READ_COMMITTED":
        print(
            "Interpretación: si el saldo final es mucho mayor que "
            f"{expected_if_atomic:.0f}, hubo actualizaciones perdidas "
            "(varios OK sobreescribieron el mismo valor leído)."
        )
    else:
        print(
            "Interpretación: SERIALIZABLE aborta carreras; con reintentos el saldo "
            "debe alinearse con 1000 − OK."
        )
        if abs(final - expected_if_atomic) > 0.5:
            print(
                "AVISO: saldo no cuadra con OK; suba RETRIES o revise errores.",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
