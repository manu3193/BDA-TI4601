#!/usr/bin/env python3
"""Paso 5 — tipo de cambio y monto ajustado (análogo a answer.py)."""

from __future__ import annotations

import csv
from pathlib import Path

from aggregate import aggregate
from join import join_names, load_names
from read import load_transactions
from transform import transform

ROOT = Path(__file__).resolve().parent


def load_rates(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["currency"]: float(row["rate"]) for row in csv.DictReader(fh)}


def adjust(joint: list[dict], rates: dict[str, float]) -> list[dict]:
    out = []
    for row in joint:
        rate = rates[row["currency"]]
        out.append(
            {
                "customer_id": row["customer_id"],
                "name": row["name"],
                "date": row["date"],
                "adjusted_amount": row["amount"] * rate,
            }
        )
    return out


if __name__ == "__main__":
    stats = aggregate(transform(load_transactions(ROOT / "transactions.csv")))
    joint = join_names(stats, load_names(ROOT / "names.csv"))
    final = adjust(joint, load_rates(ROOT / "exchange_rates.csv"))
    print("customer_id | name | date | adjusted_amount")
    print("-" * 50)
    for row in final:
        print(
            f"{row['customer_id']} | {row['name']} | {row['date']} | "
            f"{row['adjusted_amount']}"
        )
