#!/usr/bin/env python3
"""Conexión al motor del curso vía variables PG* inyectadas por Compose (libpq)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Abre conexión; el caller usa ``with conn.transaction():`` para ACID."""
    # Sin DSN explícito: libpq lee PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGSSLMODE.
    conn = psycopg.connect(row_factory=dict_row, autocommit=False)
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    with connect() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())
