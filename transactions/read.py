#!/usr/bin/env python3
"""Paso 1 — leer transacciones (transacción explícita de solo lectura)."""

from __future__ import annotations

from dbutil import connect


def load_transactions() -> list[dict]:
    with connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT customer_id, amount::float AS amount, purchased_at
                    FROM transactions
                    ORDER BY customer_id, purchased_at
                    """
                )
                return list(cur.fetchall())


def show(rows: list[dict], limit: int = 20) -> None:
    cols = ["customer_id", "amount", "purchased_at"]
    print(" | ".join(cols))
    print("-" * 50)
    for row in rows[:limit]:
        print(" | ".join(str(row[c]) for c in cols))
    print(f"\n{len(rows)} filas (motor SQL)")


if __name__ == "__main__":
    show(load_transactions())
