#!/usr/bin/env python3
"""Paso 2 — transformar fechas (análogo a bigdataclass/transactions/transform.py)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from read import load_transactions

ROOT = Path(__file__).resolve().parent


def transform(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        purchased = datetime.fromisoformat(row["purchased_at"])
        date_string = purchased.strftime("%m/%d/%Y")
        out.append(
            {
                **row,
                "date_string": date_string,
                "date": datetime.strptime(date_string, "%m/%d/%Y").date(),
            }
        )
    return out


if __name__ == "__main__":
    rows = transform(load_transactions(ROOT / "transactions.csv"))
    print("Con date_string y date tipada:\n")
    cols = ["customer_id", "amount", "purchased_at", "date_string", "date"]
    print(" | ".join(cols))
    print("-" * 70)
    for row in rows:
        print(" | ".join(str(row[c]) for c in cols))
