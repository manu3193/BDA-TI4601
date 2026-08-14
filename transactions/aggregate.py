#!/usr/bin/env python3
"""Paso 3 — agregar en el motor vía TEMP TABLE."""

from __future__ import annotations

from dbutil import connect


def aggregate() -> list[dict]:
    with connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TEMP TABLE tx_daily AS
                    SELECT
                      customer_id,
                      purchased_at::date AS date,
                      sum(amount) AS amount
                    FROM transactions
                    GROUP BY customer_id, purchased_at::date
                    """
                )
                cur.execute(
                    """
                    SELECT customer_id, date, amount::float AS amount
                    FROM tx_daily
                    ORDER BY customer_id, date
                    """
                )
                return list(cur.fetchall())


if __name__ == "__main__":
    rows = aggregate()
    print("customer_id | date | amount")
    print("-" * 40)
    for row in rows:
        print(f"{row['customer_id']} | {row['date']} | {row['amount']}")
    print(f"\n{len(rows)} filas (agregación en el motor)")
