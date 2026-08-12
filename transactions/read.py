#!/usr/bin/env python3
"""Paso 1 — leer transactions.csv (Python puro; análogo a bigdataclass/transactions/read.py)."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_transactions(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row["customer_id"] = int(row["customer_id"])
        row["amount"] = float(row["amount"])
    return rows


def show(rows: list[dict], limit: int = 20) -> None:
    cols = ["customer_id", "amount", "purchased_at"]
    print(" | ".join(cols))
    print("-" * 50)
    for row in rows[:limit]:
        print(" | ".join(str(row[c]) for c in cols))
    print(f"\n{len(rows)} filas")


if __name__ == "__main__":
    show(load_transactions(ROOT / "transactions.csv"))
