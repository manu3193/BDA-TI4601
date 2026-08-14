#!/usr/bin/env python3
"""Paso 5 — pipeline completo ACID: TEMP TABLE → join FX → resultado."""

from __future__ import annotations

from dbutil import connect


def answer() -> list[dict]:
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
                      n.customer_id,
                      n.name,
                      n.date,
                      (n.amount * e.rate)::float AS adjusted_amount
                    FROM tx_named n
                    JOIN exchange_rates e ON e.currency = n.currency
                    ORDER BY n.customer_id, n.date
                    """
                )
                return list(cur.fetchall())


if __name__ == "__main__":
    rows = answer()
    print("customer_id | name | date | adjusted_amount")
    print("-" * 50)
    for row in rows:
        print(
            f"{row['customer_id']} | {row['name']} | {row['date']} | "
            f"{row['adjusted_amount']}"
        )
    print(f"\n{len(rows)} filas (pipeline ACID + TEMP TABLE)")
