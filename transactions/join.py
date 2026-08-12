#!/usr/bin/env python3
"""Paso 4 — join con names.csv (análogo a join.py)."""

from __future__ import annotations

import csv
from pathlib import Path

from aggregate import aggregate
from read import load_transactions
from transform import transform

ROOT = Path(__file__).resolve().parent


def load_names(path: Path) -> dict[int, dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        # Cabeceras Big Data: ID,Name,Currency
        return {
            int(row["ID"]): {
                "name": row["Name"],
                "currency": row["Currency"],
            }
            for row in reader
        }


def join_names(stats: list[dict], names: dict[int, dict]) -> list[dict]:
    out = []
    for row in stats:
        info = names[row["customer_id"]]
        out.append({**row, **info})
    return out


if __name__ == "__main__":
    stats = aggregate(transform(load_transactions(ROOT / "transactions.csv")))
    joint = join_names(stats, load_names(ROOT / "names.csv"))
    print("customer_id | name | currency | date | amount")
    print("-" * 55)
    for row in joint:
        print(
            f"{row['customer_id']} | {row['name']} | {row['currency']} | "
            f"{row['date']} | {row['amount']}"
        )
