#!/usr/bin/env python3
"""Instala únicamente la licencia docente; no configura el laboratorio."""

from __future__ import annotations

import os

import psycopg
from psycopg import sql


def main() -> int:
    value = os.environ.get("COCKROACH_LICENSE", "").strip()
    if not value:
        print("COCKROACH_LICENSE está vacía; no se realizó ningún cambio.")
        print("Un clúster v24.3.0 nuevo puede usar la gracia inicial de siete días.")
        return 0

    with psycopg.connect(autocommit=True) as conn:
        conn.execute(
            sql.SQL("SET CLUSTER SETTING enterprise.license = {}").format(
                sql.Literal(value)
            )
        )
    print("Licencia instalada. El valor no se imprimió.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

