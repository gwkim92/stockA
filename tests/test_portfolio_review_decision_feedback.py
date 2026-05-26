from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.operations.portfolio_review_decision_feedback import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    build_portfolio_review_decision_feedback,
    render_portfolio_review_decision_feedback_evidence_sql,
    render_portfolio_review_decision_feedback_insert_sql,
    render_portfolio_review_decision_history_lookup_sql,
    run_portfolio_review_decision_feedback,
)


class FakeFeedbackExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return "9201"
        if "insert into ai.eval_run" in lowered:
            return "8201"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioReviewDecisionFeedbackTests(unittest.TestCase):
    def test_build_feedback_marks_young_decisions_too_early(self) -> None:
        feedback = build_portfolio_review_decision_feedback(
            history_eval=_history_eval(),
            evidence={"paper_validation": {}, "items": []},
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            min_horizon_days=30,
        )

        self.assertEqual(feedback["eval_name"], DEFAULT_EVAL_NAME)
        self.assertEqual(feedback["dataset_version"], DEFAULT_DATASET_VERSION)
        self.assertEqual(feedback["feedback_status"], "too_early")
        self.assertEqual(feedback["decision_count"], 2)
        self.assertEqual(feedback["too_early_count"], 2)
        self.assertEqual(feedback["validated_count"], 0)
        self.assertFalse(feedback["guardrails"]["automatic_order_allowed"])
        self.assertFalse(feedback["guardrails"]["broker_submit_allowed"])

    def test_reduce_decision_with_negative_outcome_is_validated(self) -> None:
        feedback = build_portfolio_review_decision_feedback(
            history_eval=_history_eval(as_of_date="2026-04-01"),
            evidence={
                "paper_validation": {},
                "items": [
                    {
                        "decision_index": 1,
                        "symbol": "TSLA",
                        "recommendation_outcome": {
                            "outcome_id": 31,
                            "recommendation_id": 61,
                            "measurement_end_date": "2026-05-15",
                            "horizon_days": 30,
                            "absolute_return_pct": "-0.0800",
                            "alpha_pct": "-0.0500",
                            "outcome_label": "underperform",
                        },
                    }
                ],
            },
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            min_horizon_days=30,
        )

        self.assertEqual(feedback["latest_items"][0]["feedback_status"], "validated")
        self.assertEqual(feedback["validated_count"], 1)
        self.assertEqual(feedback["needs_more_data_count"], 1)

    def test_reduce_decision_with_positive_outcome_is_contradicted(self) -> None:
        feedback = build_portfolio_review_decision_feedback(
            history_eval=_history_eval(as_of_date="2026-04-01"),
            evidence={
                "paper_validation": {},
                "items": [
                    {
                        "decision_index": 1,
                        "symbol": "TSLA",
                        "recommendation_outcome": {
                            "outcome_id": 32,
                            "recommendation_id": 61,
                            "measurement_end_date": "2026-05-15",
                            "horizon_days": 30,
                            "absolute_return_pct": "0.1200",
                            "alpha_pct": "0.0700",
                            "outcome_label": "outperform",
                        },
                    }
                ],
            },
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            min_horizon_days=30,
        )

        self.assertEqual(feedback["feedback_status"], "has_contradictions")
        self.assertEqual(feedback["latest_items"][0]["feedback_status"], "contradicted")
        self.assertEqual(feedback["contradicted_count"], 1)

    def test_mature_decision_without_evidence_needs_more_data(self) -> None:
        feedback = build_portfolio_review_decision_feedback(
            history_eval=_history_eval(as_of_date="2026-04-01"),
            evidence={"paper_validation": {}, "items": []},
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            min_horizon_days=30,
        )

        self.assertEqual(feedback["feedback_status"], "needs_more_data")
        self.assertEqual(feedback["needs_more_data_count"], 2)

    def test_sql_renderers_are_read_only_and_reference_expected_tables(self) -> None:
        lookup_sql = render_portfolio_review_decision_history_lookup_sql(portfolio_name="Long Term Paper")
        evidence_sql = render_portfolio_review_decision_feedback_evidence_sql(
            decision_inputs=[
                {
                    "decision_index": 1,
                    "symbol": "TSLA",
                    "decision_type": "reduce_watch",
                    "decision_family": "benchmark_drift",
                    "related_recommendation_id": 61,
                    "related_thesis_id": 1,
                }
            ],
            portfolio_name="Long Term Paper",
            history_as_of_date=date(2026, 5, 25),
            feedback_as_of_date=date(2026, 5, 27),
        )
        lowered = f"{lookup_sql}\n{evidence_sql}".lower()

        self.assertIn("from ai.eval_run", lowered)
        self.assertIn("performance.recommendation_outcome", lowered)
        self.assertIn("performance.thesis_outcome", lowered)
        self.assertIn("trading.paper_validation_run", lowered)
        self.assertIn("market.daily_price_bar", lowered)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("join broker", lowered)

    def test_insert_records_eval_run_without_weight_or_order_mutation(self) -> None:
        sql = render_portfolio_review_decision_feedback_insert_sql(
            score_json={
                "feedback_status": "too_early",
                "guardrails": {"broker_submit_allowed": False},
            }
        )
        lowered = sql.lower()

        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn(DEFAULT_EVAL_NAME, sql)
        self.assertIn(DEFAULT_DATASET_VERSION, sql)
        self.assertNotIn("signal.recommendation_score_component", lowered)
        self.assertNotIn("portfolio.position_snapshot", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_run_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeFeedbackExecutor()
        with patch(
            "stockanalysis.operations.portfolio_review_decision_feedback.load_portfolio_review_decision_history_eval",
            return_value=_history_eval(),
        ), patch(
            "stockanalysis.operations.portfolio_review_decision_feedback.load_portfolio_review_decision_feedback_evidence",
            return_value={"paper_validation": {}, "items": []},
        ):
            report = run_portfolio_review_decision_feedback(
                config=type("Config", (), {"psql_command": "psql"})(),
                portfolio_name="Long Term Paper",
                as_of_date=date(2026, 5, 27),
                execute=True,
                executor=executor,
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9201)
        self.assertEqual(report["eval_run_id"], 8201)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[1].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])


def _history_eval(*, as_of_date: str = "2026-05-25") -> dict[str, object]:
    return {
        "eval_run_id": 52,
        "created_at": "2026-05-27T02:00:00+00:00",
        "score_json": {
            "portfolio_name": "Long Term Paper",
            "as_of_date": as_of_date,
            "decisions": [
                {
                    "decision_family": "benchmark_drift",
                    "symbol": "TSLA",
                    "priority": 1,
                    "decision_type": "reduce_watch",
                    "decision_label": "비중 축소 검토",
                    "severity": "high",
                    "current_weight": 0.3068,
                    "benchmark_weight": 0.01839095,
                    "active_weight": 0.28840905,
                    "related_thesis_id": "thesis-1",
                    "related_recommendation_id": "recommendation-61",
                    "rationale": "TSLA active weight가 크다.",
                },
                {
                    "decision_family": "position_sizing",
                    "symbol": "AAPL",
                    "priority": 2,
                    "decision_type": "add_blocked_until_evidence",
                    "decision_label": "증거 전 비중 확대 금지",
                    "severity": "medium",
                    "current_weight": 0.05,
                    "related_thesis_id": "thesis-7001",
                    "related_recommendation_id": "recommendation-7101",
                    "rationale": "증거가 채워지기 전에는 비중 확대 후보로 쓰지 않는다.",
                },
            ],
        },
    }


if __name__ == "__main__":
    unittest.main()
