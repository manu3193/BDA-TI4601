#!/usr/bin/env python3
"""Paso 3 — agregar monto por cliente y día (análogo a aggregate.py)."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from read import load_transactions
from transform import transform

ROOT = Path(__file__).resolve().parent


def aggregate(rows: list[dict]) -> list[dict]:
    totals: dict[tuple, float] = defaultdict(float)
    for row in rows:
        key = (row["customer_id"], row["date"])
        totals[key] += row["amount"]
    return [
        {"customer_id": cid, "date": day, "amount": amount}
        for (cid, day), amount in sorted(totals.items())
    ]


if __name__ == "__main__":
    rows = aggregate(transform(load_transactions(ROOT / "transactions.csv")))
    print("customer_id | date | amount")
    print("-" * 40)
    for row in rows:
        print(f"{row['customer_id']} | {row['date']} | {row['amount']}")
