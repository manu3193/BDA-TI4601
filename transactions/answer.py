#!/usr/bin/env python3
"""Paso 5 — tipo de cambio y monto ajustado en Postgres."""

from __future__ import annotations

from dbutil import fetch_all


def answer() -> list[dict]:
    return fetch_all(
        """
        SELECT
          t.customer_id,
          c.name,
          t.purchased_at::date AS date,
          (sum(t.amount) * e.rate)::float AS adjusted_amount
        FROM transactions t
        JOIN customers c ON c.id = t.customer_id
        JOIN exchange_rates e ON e.currency = c.currency
        GROUP BY t.customer_id, c.name, t.purchased_at::date, e.rate
        ORDER BY t.customer_id, date
        """
    )


if __name__ == "__main__":
    rows = answer()
    print("customer_id | name | date | adjusted_amount")
    print("-" * 50)
    for row in rows:
        print(
            f"{row['customer_id']} | {row['name']} | {row['date']} | "
            f"{row['adjusted_amount']}"
        )
    print(f"\n{len(rows)} filas (fuente: Postgres)")
