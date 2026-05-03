from __future__ import annotations

import unittest

from stockanalysis.frontend.db_pool import PsycopgPoolExecutor
from stockanalysis.ingest.psql import PsqlExecutionError


class FakeCursor:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row
        self.executed_sql: list[str] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, sql: str) -> None:
        self.executed_sql.append(sql)

    def fetchone(self) -> tuple[object, ...] | None:
        return self.row


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self._cursor


class FakePool:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.cursor = FakeCursor(row)

    def connection(self) -> FakeConnection:
        return FakeConnection(self.cursor)


class PsycopgPoolExecutorTests(unittest.TestCase):
    def test_execute_scalar_returns_first_column_as_text(self) -> None:
        pool = FakePool(('{"status":"ok"}',))
        executor = PsycopgPoolExecutor(pool)

        result = executor.execute_scalar("select json_build_object('status', 'ok')::text")

        self.assertEqual(result, '{"status":"ok"}')
        self.assertEqual(pool.cursor.executed_sql, ["select json_build_object('status', 'ok')::text"])

    def test_execute_scalar_rejects_empty_result(self) -> None:
        executor = PsycopgPoolExecutor(FakePool(None))

        with self.assertRaises(PsqlExecutionError):
            executor.execute_scalar("select null where false")

    def test_execute_non_query_runs_sql(self) -> None:
        pool = FakePool(("ignored",))
        executor = PsycopgPoolExecutor(pool)

        executor.execute_non_query("select 1")

        self.assertEqual(pool.cursor.executed_sql, ["select 1"])


if __name__ == "__main__":
    unittest.main()
