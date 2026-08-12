#!/usr/bin/env python3
"""Paso 2 — transformar fechas en Postgres."""

from __future__ import annotations

from dbutil import fetch_all


def transform() -> list[dict]:
    return fetch_all(
        """
        SELECT
          customer_id,
          amount::float AS amount,
          purchased_at,
          to_char(purchased_at, 'MM/DD/YYYY') AS date_string,
          purchased_at::date AS date
        FROM transactions
        ORDER BY customer_id, purchased_at
        """
    )


if __name__ == "__main__":
    rows = transform()
    cols = ["customer_id", "amount", "purchased_at", "date_string", "date"]
    print(" | ".join(cols))
    print("-" * 70)
    for row in rows:
        print(" | ".join(str(row[c]) for c in cols))
    print(f"\n{len(rows)} filas (fuente: Postgres)")
