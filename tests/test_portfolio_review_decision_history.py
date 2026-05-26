from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.operations.portfolio_review_decision_history import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    build_portfolio_review_decision_history,
    render_portfolio_review_decision_history_insert_sql,
    run_portfolio_review_decision_history,
)


class FakeDecisionHistoryExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return "9101"
        if "insert into ai.eval_run" in lowered:
            return "8101"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioReviewDecisionHistoryTests(unittest.TestCase):
    def test_build_history_preserves_review_decisions_and_read_only_guardrails(self) -> None:
        history = build_portfolio_review_decision_history(
            portfolio_coverage=_coverage_payload(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 25),
        )

        self.assertEqual(history["eval_name"], DEFAULT_EVAL_NAME)
        self.assertEqual(history["dataset_version"], DEFAULT_DATASET_VERSION)
        self.assertEqual(history["decision_status"], "review_required")
        self.assertEqual(history["decision_count"], 2)
        self.assertEqual(history["benchmark_decision_count"], 1)
        self.assertEqual(history["position_sizing_decision_count"], 1)
        self.assertEqual(history["decision_counts"]["reduce_watch"], 1)
        self.assertEqual(history["decision_counts"]["add_blocked_until_evidence"], 1)
        self.assertEqual(history["top_decision"]["symbol"], "TSLA")
        self.assertEqual(history["latest_decisions"][0]["source_evidence"]["benchmark_code"], "SPY")
        self.assertEqual(history["latest_decisions"][1]["related_recommendation_id"], "recommendation-7101")
        self.assertFalse(history["guardrails"]["recommendation_scoring_mutated"])
        self.assertFalse(history["guardrails"]["automatic_order_allowed"])
        self.assertFalse(history["guardrails"]["broker_submit_allowed"])
        self.assertEqual(history["guardrails"]["order_boundary"], "read_only_no_order")

    def test_render_insert_uses_eval_run_without_weight_or_order_mutation(self) -> None:
        sql = render_portfolio_review_decision_history_insert_sql(
            score_json={
                "portfolio_name": "Long Term Paper",
                "decision_status": "review_required",
                "guardrails": {"broker_submit_allowed": False},
            }
        )
        lowered = sql.lower()

        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn(DEFAULT_EVAL_NAME, sql)
        self.assertIn(DEFAULT_DATASET_VERSION, sql)
        self.assertNotIn("signal.recommendation_score_component", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_run_preview_does_not_write_eval_run(self) -> None:
        executor = FakeDecisionHistoryExecutor()
        with patch(
            "stockanalysis.operations.portfolio_review_decision_history.load_portfolio_review_decision_source",
            return_value=_coverage_payload(),
        ):
            report = run_portfolio_review_decision_history(
                config=type("Config", (), {"psql_command": "psql"})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2026, 5, 25),
                execute=False,
                executor=executor,
            )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["decision"]["decision_count"], 2)
        self.assertEqual(executor.scalar_sql, [])
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeDecisionHistoryExecutor()
        with patch(
            "stockanalysis.operations.portfolio_review_decision_history.load_portfolio_review_decision_source",
            return_value=_coverage_payload(),
        ):
            report = run_portfolio_review_decision_history(
                config=type("Config", (), {"psql_command": "psql"})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2026, 5, 25),
                execute=True,
                executor=executor,
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9101)
        self.assertEqual(report["eval_run_id"], 8101)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[1].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])


def _coverage_payload() -> dict[str, object]:
    return {
        "portfolio_name": "Long Term Paper",
        "as_of_date": "2026-05-25",
        "coverage_measurement_end_date": "2026-06-25",
        "risk_budget": {
            "status": "needs_position_review",
            "rebalance_candidate_review": {
                "status": "review_required",
                "candidates": [
                    {
                        "priority": 1,
                        "symbol": "TSLA",
                        "current_weight": 0.3068,
                        "benchmark_weight": 0.01839095,
                        "active_weight": 0.28840905,
                        "severity": "high",
                        "review_decision": "reduce_watch",
                        "decision_label": "비중 축소 검토",
                        "next_review_action": "추가 매수를 막고 축소 여부만 검토한다.",
                        "source_evidence": {
                            "benchmark_code": "SPY",
                            "benchmark_source": "ssga_spdr_spy_daily_holdings",
                            "review_threshold_active_weight": 0.03,
                        },
                        "related_thesis_id": "thesis-1",
                        "related_recommendation_id": "recommendation-61",
                        "related_recommendation_action": "hold",
                        "related_recommended_weight": 0.04,
                        "links": {"stock": "/stocks/TSLA"},
                        "decision_path": [{"step": "order_boundary", "label": "주문 금지", "detail": ""}],
                        "rationale": "TSLA active weight가 크다.",
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    }
                ],
            },
            "position_sizing_review": {
                "status": "review_required",
                "candidates": [
                    {
                        "priority": 1,
                        "symbol": "AAPL",
                        "instrument_id": "instrument-501",
                        "current_weight": 0.05,
                        "benchmark_weight": 0.07,
                        "active_weight": -0.02,
                        "severity": "medium",
                        "review_band": "add_blocked_until_evidence",
                        "policy_ceiling_weight": 0.25,
                        "review_ceiling_weight": 0.17,
                        "related_thesis_id": "thesis-7001",
                        "related_recommendation_id": "recommendation-7101",
                        "related_recommendation_action": "monitor_or_accumulate",
                        "related_recommended_weight": 0.05,
                        "links": {"stock": "/stocks/AAPL", "recommendation": "/recommendations/recommendation-7101"},
                        "thesis_status": "connected",
                        "professional_analysis_status": "partial",
                        "blocking_factors": ["valuation_unavailable"],
                        "supporting_factors": ["thesis_connected"],
                        "rationale": "증거가 채워지기 전에는 비중 확대 후보로 쓰지 않는다.",
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    }
                ],
            },
        },
    }


if __name__ == "__main__":
    unittest.main()
