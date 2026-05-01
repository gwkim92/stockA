from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from stockanalysis.ingest.portfolio.position import (
    load_position_snapshot_sync_result,
    render_position_snapshot_upsert_sql,
    run_position_snapshot_upsert,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 7001,
        portfolio_id: int = 3001,
        position_count: int = 1,
        linked_thesis_count: int = 1,
        fail_on_upsert: bool = False,
    ) -> None:
        self.run_id = run_id
        self.portfolio_id = portfolio_id
        self.position_count = position_count
        self.linked_thesis_count = linked_thesis_count
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into portfolio.position_snapshot" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return json.dumps(
                {
                    "portfolio_id": self.portfolio_id,
                    "source_position_count": 1,
                    "position_count": self.position_count,
                    "linked_thesis_count": self.linked_thesis_count,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PositionSnapshotIngestTests(unittest.TestCase):
    def test_load_position_snapshot_sync_result_from_csv(self) -> None:
        result = load_position_snapshot_sync_result(
            positions_csv_path=str(FIXTURES_DIR / "portfolio_positions_long_term_paper.csv"),
            portfolio_name="Long Term Paper",
            strategy_name="long_term_core",
            snapshot_date=date(2024, 11, 1),
        )
        self.assertEqual(result.portfolio_name, "Long Term Paper")
        self.assertEqual(result.base_currency, "USD")
        self.assertEqual(result.market_code, "US")
        self.assertEqual(len(result.positions), 1)
        self.assertEqual(result.positions[0].symbol, "AAPL")
        self.assertEqual(result.positions[0].quantity, Decimal("10.00000000"))
        self.assertEqual(result.positions[0].weight, Decimal("0.0500"))
        self.assertEqual(result.positions[0].linked_thesis_id, None)

    def test_load_position_snapshot_sync_result_rejects_missing_required_columns(self) -> None:
        fixture_path = FIXTURES_DIR / "portfolio_positions_long_term_paper.csv"
        bad_path = fixture_path.parent / "portfolio_positions_missing_required.tmp.csv"
        bad_path.write_text("symbol,quantity\nAAPL,10\n", encoding="utf-8")
        try:
            with self.assertRaises(ValueError):
                load_position_snapshot_sync_result(
                    positions_csv_path=str(bad_path),
                    portfolio_name="Long Term Paper",
                    strategy_name="long_term_core",
                    snapshot_date=date(2024, 11, 1),
                )
        finally:
            bad_path.unlink(missing_ok=True)

    def test_render_position_snapshot_upsert_sql(self) -> None:
        result = load_position_snapshot_sync_result(
            positions_csv_path=str(FIXTURES_DIR / "portfolio_positions_long_term_paper.csv"),
            portfolio_name="Long Term Paper",
            strategy_name="long_term_core",
            snapshot_date=date(2024, 11, 1),
        )
        sql = render_position_snapshot_upsert_sql(result, source_run_id=77)
        self.assertIn("insert into portfolio.portfolio", sql)
        self.assertIn("insert into portfolio.position_snapshot", sql)
        self.assertIn("left join lateral", sql)
        self.assertIn("'Long Term Paper'", sql)
        self.assertIn("'AAPL'", sql)
        self.assertIn("0.0500::numeric", sql)
        self.assertIn("77::bigint", sql)

    def test_run_position_snapshot_upsert_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=7002, portfolio_id=3002)
        summary = run_position_snapshot_upsert(
            config=type("Config", (), {})(),
            positions_csv_path=str(FIXTURES_DIR / "portfolio_positions_long_term_paper.csv"),
            portfolio_name="Long Term Paper",
            strategy_name="long_term_core",
            snapshot_date=date(2024, 11, 1),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 7002)
        self.assertEqual(summary["portfolio_id"], 3002)
        self.assertEqual(summary["position_count"], 1)
        self.assertEqual(summary["linked_thesis_count"], 1)
        self.assertEqual(summary["symbol_preview"], ["AAPL"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("insert into portfolio.position_snapshot", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_position_snapshot_upsert_marks_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=7003, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_position_snapshot_upsert(
                config=type("Config", (), {})(),
                positions_csv_path=str(FIXTURES_DIR / "portfolio_positions_long_term_paper.csv"),
                portfolio_name="Long Term Paper",
                strategy_name="long_term_core",
                snapshot_date=date(2024, 11, 1),
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])

    def test_run_position_snapshot_upsert_fails_when_symbol_not_matched(self) -> None:
        executor = FakeExecutor(run_id=7004, position_count=0, linked_thesis_count=0)
        with self.assertRaises(ValueError):
            run_position_snapshot_upsert(
                config=type("Config", (), {})(),
                positions_csv_path=str(FIXTURES_DIR / "portfolio_positions_long_term_paper.csv"),
                portfolio_name="Long Term Paper",
                strategy_name="long_term_core",
                snapshot_date=date(2024, 11, 1),
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
