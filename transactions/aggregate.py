#!/usr/bin/env python3
"""Paso 3 — agregar monto por cliente y día en Postgres."""

from __future__ import annotations

from dbutil import fetch_all


def aggregate() -> list[dict]:
    return fetch_all(
        """
        SELECT
          customer_id,
          purchased_at::date AS date,
          sum(amount)::float AS amount
        FROM transactions
        GROUP BY customer_id, purchased_at::date
        ORDER BY customer_id, date
        """
    )


if __name__ == "__main__":
    rows = aggregate()
    print("customer_id | date | amount")
    print("-" * 40)
    for row in rows:
        print(f"{row['customer_id']} | {row['date']} | {row['amount']}")
    print(f"\n{len(rows)} filas (fuente: Postgres)")
