#!/usr/bin/env python3
"""Paso 2 — proyectar fechas en el servidor (sin DataFrame en el cliente)."""

from __future__ import annotations

from dbutil import connect


def transform() -> list[dict]:
    with connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                # TEMP TABLE: trabajo intermedio vive en el backend, no en RAM del cliente.
                cur.execute(
                    """
                    CREATE TEMP TABLE tx_enriched AS
                    SELECT
                      customer_id,
                      amount,
                      purchased_at,
                      to_char(purchased_at, 'MM/DD/YYYY') AS date_string,
                      purchased_at::date AS date
                    FROM transactions
                    """
                )
                cur.execute(
                    """
                    SELECT
                      customer_id,
                      amount::float AS amount,
                      purchased_at,
                      date_string,
                      date
                    FROM tx_enriched
                    ORDER BY customer_id, purchased_at
                    """
                )
                return list(cur.fetchall())


if __name__ == "__main__":
    rows = transform()
    cols = ["customer_id", "amount", "purchased_at", "date_string", "date"]
    print(" | ".join(cols))
    print("-" * 70)
    for row in rows:
        print(" | ".join(str(row[c]) for c in cols))
    print(f"\n{len(rows)} filas (TEMP TABLE en el motor)")
