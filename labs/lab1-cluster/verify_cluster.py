#!/usr/bin/env python3
"""Verifica el trabajo del estudiante sin configurar ni corregir el clúster."""

from __future__ import annotations

import sys
from collections.abc import Callable

import psycopg


EXPECTED_REGIONS = {"cr-sj", "cr-limon", "us-east"}


def live_regions(conn: psycopg.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT locality FROM crdb_internal.gossip_nodes WHERE is_live"
    ).fetchall()
    return {
        item.removeprefix("region=")
        for row in rows
        for item in str(row[0]).split(",")
        if item.startswith("region=")
    }


def raft_probe_has_three_voters(conn: psycopg.Connection) -> bool:
    rows = conn.execute(
        """
        SELECT voting_replicas
        FROM [SHOW RANGES FROM TABLE
              ti4601_raft.public.raft_probe WITH DETAILS]
        """
    ).fetchall()
    return bool(rows) and all(len(row[0]) == 3 for row in rows)


def check(label: str, assertion: Callable[[], bool], hint: str) -> bool:
    try:
        passed = assertion()
    except (psycopg.Error, IndexError, TypeError) as exc:
        print(f"[FAIL] {label}: {str(exc).splitlines()[0]}")
        print(f"       Pista: {hint}")
        return False
    if passed:
        print(f"[ OK ] {label}")
        return True
    print(f"[FAIL] {label}")
    print(f"       Pista: {hint}")
    return False


def main() -> int:
    try:
        conn = psycopg.connect(autocommit=True)
    except psycopg.Error as exc:
        print(f"[FAIL] conexión: {str(exc).splitlines()[0]}")
        print("       Pista: levante los tres nodos y compruebe `make lab1-status`.")
        return 1

    with conn:
        results = [
            check(
                "tres nodos/localities vivos",
                lambda: EXPECTED_REGIONS <= live_regions(conn),
                "revise localities y logs de crdb-1, crdb-2 y crdb-3",
            ),
            check(
                "tres regiones configuradas",
                lambda: EXPECTED_REGIONS
                <= {
                    str(row[1])
                    for row in conn.execute(
                        "SHOW REGIONS FROM DATABASE ti4601"
                    ).fetchall()
                },
                "ejecute PRIMARY REGION y ADD REGION en el orden de la guía",
            ),
            check(
                "catalogo_producto es GLOBAL",
                lambda: "LOCALITY GLOBAL"
                in str(
                    conn.execute("SHOW CREATE TABLE catalogo_producto").fetchone()[1]
                ).upper(),
                "aplique schema.sql después de configurar las regiones",
            ),
            check(
                "pedido es REGIONAL BY ROW",
                lambda: "REGIONAL BY ROW"
                in str(conn.execute("SHOW CREATE TABLE pedido").fetchone()[1]).upper(),
                "revise la columna region y la cláusula LOCALITY de schema.sql",
            ),
            check(
                "hay una fila pedido por región",
                lambda: EXPECTED_REGIONS
                == {
                    str(row[0])
                    for row in conn.execute(
                        "SELECT DISTINCT region FROM pedido"
                    ).fetchall()
                },
                "aplique seed.sql y consulte GROUP BY region",
            ),
            check(
                "raft_probe tiene tres votantes",
                lambda: raft_probe_has_three_voters(conn),
                "aplique raft_probe.sql y espere la replicación antes del chaos",
            ),
        ]

    passed = sum(results)
    print(f"\nResultado: {passed}/{len(results)} verificaciones.")
    if passed != len(results):
        print("El verificador no modificó el clúster. Corrija el primer FAIL y repita.")
        return 1
    print("Configuración lista para mediciones y Chaos A.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

