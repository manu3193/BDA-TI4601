#!/usr/bin/env python3
"""Paso 4 — join + agregación en TEMP TABLE."""

from __future__ import annotations

from dbutil import connect


def join_names() -> list[dict]:
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
                    CREATE TEMP TABLE tx_named AS
                    SELECT
                      d.customer_id,
                      c.name,
                      c.currency,
                      d.date,
                      d.amount
                    FROM tx_daily d
                    JOIN customers c ON c.id = d.customer_id
                    """
                )
                cur.execute(
                    """
                    SELECT
                      customer_id,
                      name,
                      currency,
                      date,
                      amount::float AS amount
                    FROM tx_named
                    ORDER BY customer_id, date
                    """
                )
                return list(cur.fetchall())


if __name__ == "__main__":
    rows = join_names()
    print("customer_id | name | currency | date | amount")
    print("-" * 55)
    for row in rows:
        print(
            f"{row['customer_id']} | {row['name']} | {row['currency']} | "
            f"{row['date']} | {row['amount']}"
        )
    print(f"\n{len(rows)} filas (join en el motor)")
