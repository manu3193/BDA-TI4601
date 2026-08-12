#!/usr/bin/env python3
"""Paso 1 — leer transacciones desde Postgres."""

from __future__ import annotations

from dbutil import fetch_all


def load_transactions() -> list[dict]:
    return fetch_all(
        """
        SELECT customer_id, amount::float AS amount, purchased_at
        FROM transactions
        ORDER BY customer_id, purchased_at
        """
    )


def show(rows: list[dict], limit: int = 20) -> None:
    cols = ["customer_id", "amount", "purchased_at"]
    print(" | ".join(cols))
    print("-" * 50)
    for row in rows[:limit]:
        print(" | ".join(str(row[c]) for c in cols))
    print(f"\n{len(rows)} filas (fuente: Postgres)")


if __name__ == "__main__":
    show(load_transactions())
