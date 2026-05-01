from __future__ import annotations

import unittest
from pathlib import Path

from stockanalysis.ingest.macro.defaults import get_default_series
from stockanalysis.ingest.macro.upsert import (
    resolve_default_macro_specs,
    run_macro_batch_upsert,
    run_macro_upsert,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 101,
        run_ids: list[int] | None = None,
        fail_on_upsert_calls: set[int] | None = None,
    ) -> None:
        self.run_id = run_id
        self.run_ids = list(run_ids) if run_ids is not None else None
        self.fail_on_upsert_calls = set(fail_on_upsert_calls or set())
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self._upsert_call_count = 0

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if self.run_ids is not None:
            if not self.run_ids:
                raise RuntimeError("no remaining run ids")
            return str(self.run_ids.pop(0))
        return str(self.run_id)

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if "insert into macro.series" in sql:
            self._upsert_call_count += 1
        if self._upsert_call_count in self.fail_on_upsert_calls and "insert into macro.series" in sql:
            raise RuntimeError("boom")


class MacroUpsertTests(unittest.TestCase):
    def test_run_macro_upsert_records_pipeline_run_and_source_run_id(self) -> None:
        spec = get_default_series("CPIAUCSL")
        assert spec is not None
        executor = FakeExecutor(run_id=77)

        summary = run_macro_upsert(
            spec,
            config=type("Config", (), {})(),
            series_json_path=str(FIXTURES_DIR / "fred_series_CPIAUCSL.json"),
            observations_json_path=str(FIXTURES_DIR / "fred_observations_CPIAUCSL.json"),
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["observation_count"], 2)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("77::bigint", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_macro_upsert_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        spec = get_default_series("CPIAUCSL")
        assert spec is not None
        executor = FakeExecutor(run_id=88, fail_on_upsert_calls={1})

        with self.assertRaises(RuntimeError):
            run_macro_upsert(
                spec,
                config=type("Config", (), {})(),
                series_json_path=str(FIXTURES_DIR / "fred_series_CPIAUCSL.json"),
                observations_json_path=str(FIXTURES_DIR / "fred_observations_CPIAUCSL.json"),
                executor=executor,
            )

        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_resolve_default_macro_specs_uses_all_defaults_when_empty(self) -> None:
        specs = resolve_default_macro_specs([])
        self.assertGreaterEqual(len(specs), 8)

    def test_run_macro_batch_upsert_uses_fixture_directory(self) -> None:
        specs = resolve_default_macro_specs(["CPIAUCSL", "FEDFUNDS"])
        executor = FakeExecutor(run_ids=[301, 302])

        summary = run_macro_batch_upsert(
            specs,
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            executor=executor,
        )

        self.assertEqual(summary["requested_series_count"], 2)
        self.assertEqual(summary["succeeded_series_count"], 2)
        self.assertEqual(summary["failed_series_count"], 0)
        self.assertEqual(summary["total_observation_count"], 5)
        self.assertEqual(summary["results"][0]["run_id"], 301)
        self.assertEqual(summary["results"][1]["run_id"], 302)

    def test_run_macro_batch_upsert_continues_after_failure(self) -> None:
        specs = resolve_default_macro_specs(["CPIAUCSL", "FEDFUNDS"])
        executor = FakeExecutor(run_ids=[401, 402], fail_on_upsert_calls={2})

        summary = run_macro_batch_upsert(
            specs,
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            executor=executor,
        )

        self.assertEqual(summary["succeeded_series_count"], 1)
        self.assertEqual(summary["failed_series_count"], 1)
        self.assertEqual(summary["results"][0]["status"], "succeeded")
        self.assertEqual(summary["results"][1]["status"], "failed")
