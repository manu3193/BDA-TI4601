#!/usr/bin/env python3
"""Paso 4 — join con customers en Postgres."""

from __future__ import annotations

from dbutil import fetch_all


def join_names() -> list[dict]:
    return fetch_all(
        """
        SELECT
          t.customer_id,
          c.name,
          c.currency,
          t.purchased_at::date AS date,
          sum(t.amount)::float AS amount
        FROM transactions t
        JOIN customers c ON c.id = t.customer_id
        GROUP BY t.customer_id, c.name, c.currency, t.purchased_at::date
        ORDER BY t.customer_id, date
        """
    )


if __name__ == "__main__":
    rows = join_names()
    print("customer_id | name | currency | date | amount")
    print("-" * 55)
    for row in rows:
        print(
            f"{row['customer_id']} | {row['name']} | {row['currency']} | "
            f"{row['date']} | {row['amount']}"
        )
    print(f"\n{len(rows)} filas (fuente: Postgres)")
