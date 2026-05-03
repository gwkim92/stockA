from __future__ import annotations

from typing import Any

from stockanalysis.ingest.psql import PsqlExecutionError


class PsycopgPoolExecutor:
    """Execute existing read-report SQL through a psycopg connection pool."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool

    def execute_scalar(self, sql: str) -> str:
        with self._pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
        if row is None:
            raise PsqlExecutionError("psycopg pool returned no rows for scalar query")
        value = row[0]
        if value is None:
            raise PsqlExecutionError("psycopg pool returned null for scalar query")
        return str(value)

    def execute_non_query(self, sql: str) -> None:
        with self._pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
