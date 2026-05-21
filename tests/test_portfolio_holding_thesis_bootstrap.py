from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.portfolio_holding_thesis import (
    PortfolioHoldingThesisCandidate,
    build_portfolio_holding_thesis_rows,
    load_portfolio_holding_thesis_candidates,
    render_portfolio_holding_thesis_candidate_lookup_sql,
    render_portfolio_holding_thesis_upsert_sql,
    run_portfolio_holding_thesis_bootstrap,
)


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 4101,
        upsert_payload: dict[str, object] | None = None,
        candidates: list[dict[str, object]] | None = None,
        fail_on_upsert: bool = False,
    ) -> None:
        self.run_id = run_id
        self.upsert_payload = upsert_payload or {
            "portfolio_id": 7,
            "portfolio_name": "Long Term Paper",
            "snapshot_date": "2026-05-21",
            "source_position_count": 1,
            "inserted_thesis_count": 1,
            "matched_existing_thesis_count": 0,
            "linked_position_count": 1,
        }
        self.candidates = candidates if candidates is not None else [_candidate_payload()]
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- portfolio holding thesis candidate lookup"):
            return json.dumps(self.candidates)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into signal.investment_thesis" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return json.dumps(self.upsert_payload)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioHoldingThesisBootstrapTests(unittest.TestCase):
    def test_render_candidate_lookup_targets_latest_unlinked_positions(self) -> None:
        sql = render_portfolio_holding_thesis_candidate_lookup_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 21),
            strategy_name="long_term_core",
            horizon_type="long_term",
            market_code="US",
        )

        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("position.linked_thesis_id is null", sql)
        self.assertIn("signal.investment_thesis thesis", sql)
        self.assertIn("signal.recommendation recommendation", sql)
        self.assertIn("portfolio_name = 'Long Term Paper'", sql)

    def test_load_candidates_allows_empty_lookup(self) -> None:
        candidates = load_portfolio_holding_thesis_candidates(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 21),
            strategy_name="long_term_core",
            horizon_type="long_term",
            executor=FakeExecutor(candidates=[]),
        )

        self.assertEqual(candidates, ())

    def test_build_rows_creates_conservative_monitor_thesis(self) -> None:
        rows = build_portfolio_holding_thesis_rows(
            (
                PortfolioHoldingThesisCandidate(
                    portfolio_id=7,
                    portfolio_name="Long Term Paper",
                    snapshot_date=date(2026, 5, 21),
                    instrument_id=501,
                    primary_symbol="AAPL",
                    weight=Decimal("0.2500"),
                    market_value=Decimal("25000.00"),
                    existing_thesis_id=None,
                    node_id=11,
                    node_code="AI_PLATFORM",
                    node_name="AI Platform",
                    cycle_state="expanding",
                    cycle_score=Decimal("0.6200"),
                    recommendation_action=None,
                    recommendation_score=None,
                ),
            ),
            strategy_name="long_term_core",
            horizon_type="long_term",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].title, "AAPL 보유 검토 thesis via AI Platform")
        self.assertEqual(rows[0].expected_holding_days, 365)
        self.assertEqual(rows[0].benchmark_code, "SPY")
        self.assertEqual(rows[0].conviction_score, Decimal("0.6200"))
        self.assertIn("자동 매수 신호가 아니라 보유 커버리지 공백", rows[0].summary)
        self.assertIn("최신 추천 조치는 추천 없음", rows[0].summary)
        self.assertIn("사람 승인으로만 축소/청산", rows[0].exit_conditions)

    def test_render_upsert_sql_reuses_existing_thesis_and_links_position(self) -> None:
        rows = build_portfolio_holding_thesis_rows(
            (
                PortfolioHoldingThesisCandidate(
                    portfolio_id=7,
                    portfolio_name="Long Term Paper",
                    snapshot_date=date(2026, 5, 21),
                    instrument_id=501,
                    primary_symbol="AAPL",
                    weight=Decimal("0.2500"),
                    market_value=Decimal("25000.00"),
                    existing_thesis_id=9901,
                    node_id=11,
                    node_code="AI_PLATFORM",
                    node_name="AI Platform",
                    cycle_state="expanding",
                    cycle_score=Decimal("0.6200"),
                    recommendation_action="watch",
                    recommendation_score=Decimal("0.4800"),
                ),
            ),
            strategy_name="long_term_core",
            horizon_type="long_term",
        )
        sql = render_portfolio_holding_thesis_upsert_sql(rows, source_run_id=77)

        self.assertIn("insert into signal.investment_thesis", sql)
        self.assertIn("update portfolio.position_snapshot position", sql)
        self.assertIn("linked_thesis_id = all_links.thesis_id", sql)
        self.assertIn("thesis.thesis_id = source_rows.existing_thesis_id", sql)
        self.assertIn("9901::bigint", sql)
        self.assertIn("77::bigint", sql)

    def test_run_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=4102)
        summary = run_portfolio_holding_thesis_bootstrap(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 21),
            strategy_name="long_term_core",
            horizon_type="long_term",
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 4102)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["thesis_count"], 1)
        self.assertEqual(summary["inserted_thesis_count"], 1)
        self.assertEqual(summary["linked_position_count"], 1)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.investment_thesis", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_bootstrap_noops_without_candidates(self) -> None:
        executor = FakeExecutor(run_id=4103, candidates=[])
        summary = run_portfolio_holding_thesis_bootstrap(
            config=type("Config", (), {})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 21),
            strategy_name="long_term_core",
            horizon_type="long_term",
            executor=executor,
        )

        self.assertEqual(summary["candidate_count"], 0)
        self.assertEqual(summary["thesis_count"], 0)
        self.assertEqual(summary["inserted_thesis_count"], 0)
        self.assertEqual(summary["linked_position_count"], 0)
        self.assertEqual(len(executor.scalar_sql), 2)
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=4104, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_portfolio_holding_thesis_bootstrap(
                config=type("Config", (), {})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2026, 5, 21),
                strategy_name="long_term_core",
                horizon_type="long_term",
                executor=executor,
            )

        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _candidate_payload() -> dict[str, object]:
    return {
        "portfolio_id": 7,
        "portfolio_name": "Long Term Paper",
        "snapshot_date": "2026-05-21",
        "instrument_id": 501,
        "primary_symbol": "AAPL",
        "weight": "0.2500",
        "market_value": "25000.00",
        "existing_thesis_id": None,
        "node_id": 11,
        "node_code": "AI_PLATFORM",
        "node_name": "AI Platform",
        "cycle_state": "expanding",
        "cycle_score": "0.6200",
        "recommendation_action": None,
        "recommendation_score": None,
    }


if __name__ == "__main__":
    unittest.main()
