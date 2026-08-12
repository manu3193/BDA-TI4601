#!/usr/bin/env python3
"""Conexión a Postgres del curso (imagen oficial vía scripts/up.sh)."""

from __future__ import annotations

import os

import psycopg
from psycopg.rows import dict_row


def connect() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5433"),
        user=os.environ.get("PGUSER", "ti4601"),
        password=os.environ.get("PGPASSWORD", "ti4601"),
        dbname=os.environ.get("PGDATABASE", "ti4601"),
        row_factory=dict_row,
    )


def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())
