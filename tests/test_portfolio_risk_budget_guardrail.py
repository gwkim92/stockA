from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.portfolio_risk_budget_guardrail import (
    DEFAULT_EVAL_NAME,
    build_portfolio_risk_budget_guardrail_report,
    render_portfolio_risk_budget_guardrail_insert_sql,
    render_portfolio_risk_budget_state_sql,
    run_portfolio_risk_budget_guardrail,
)


class FakePortfolioRiskBudgetExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.run_id = 9904
        self.eval_run_id = 604

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- portfolio risk budget guardrail state lookup"):
            return json.dumps(_guardrail_state())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.eval_run" in sql:
            return str(self.eval_run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioRiskBudgetGuardrailTests(unittest.TestCase):
    def test_render_state_lookup_is_read_only_and_uses_canonical_tables(self) -> None:
        sql = render_portfolio_risk_budget_state_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 25),
        )
        lowered = sql.lower()

        self.assertIn("-- portfolio risk budget guardrail state lookup", sql)
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("portfolio.allocation_policy", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("ref.classification_node", sql)
        self.assertIn("position.snapshot_date <= '2026-05-25'::date", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_build_report_blocks_paper_input_when_position_or_concentration_is_over_limit(self) -> None:
        report = build_portfolio_risk_budget_guardrail_report(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 25),
            state=_guardrail_state(),
        )

        self.assertEqual(report["report_name"], DEFAULT_EVAL_NAME)
        self.assertEqual(report["risk_gate_decision"], "blocked_by_risk_budget_review")
        self.assertFalse(report["risk_gate_passed"])
        self.assertFalse(report["paper_validation_input_allowed"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(report["position_summary"]["over_single_position_limit_count"], 1)
        self.assertEqual(report["concentration_summary"]["sector_over_limit_count"], 1)
        self.assertEqual(report["benchmark_drift"]["status"], "insufficient_benchmark_composition")
        self.assertFalse(report["benchmark_drift"]["drift_calculated"])
        self.assertIn("over_single_position_limit", {item["code"] for item in report["blocking_reasons"]})
        self.assertIn("sector_over_limit", {item["code"] for item in report["blocking_reasons"]})

    def test_build_report_marks_missing_snapshot_as_blocked(self) -> None:
        state = {
            **_guardrail_state(),
            "snapshot_date": None,
            "position_count": 0,
            "positions": [],
            "sector_exposures": [],
            "theme_exposures": [],
        }

        report = build_portfolio_risk_budget_guardrail_report(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 25),
            state=state,
        )

        self.assertEqual(report["risk_gate_decision"], "missing_position_snapshot")
        self.assertFalse(report["paper_validation_input_allowed"])
        self.assertEqual(report["blocking_reasons"][0]["code"], "missing_position_snapshot")

    def test_render_insert_records_eval_without_weight_or_order_mutation(self) -> None:
        sql = render_portfolio_risk_budget_guardrail_insert_sql(
            score_json={"risk_gate_decision": "blocked_by_risk_budget_review"}
        )
        lowered = sql.lower()

        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn("portfolio_risk_budget_guardrail", sql)
        self.assertNotIn("signal.recommendation_score_component", lowered)
        self.assertNotIn("trading.order_intent", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_run_execute_records_pipeline_and_eval_report(self) -> None:
        executor = FakePortfolioRiskBudgetExecutor()

        report = run_portfolio_risk_budget_guardrail(
            config=RuntimeConfig(psql_command="docker exec psql"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 25),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9904)
        self.assertEqual(report["eval_run_id"], 604)
        self.assertEqual(report["risk_gate_decision"], "blocked_by_risk_budget_review")
        self.assertIn("-- portfolio risk budget guardrail state lookup", executor.scalar_sql[0])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _guardrail_state() -> dict[str, object]:
    return {
        "portfolio_name": "Long Term Paper",
        "portfolio_found": True,
        "market_code": "US",
        "requested_as_of_date": "2026-05-25",
        "snapshot_date": "2026-05-23",
        "position_count": 3,
        "position_weight_total": "0.9200",
        "allocation_policy": {
            "allocation_policy_id": 4001,
            "policy_name": "global_default_long_term_guardrail",
            "policy_scope": "global",
            "max_single_position_weight": "0.2500",
            "min_rebalance_target_weight": "0.1000",
        },
        "positions": [
            {"instrument_id": 1, "symbol": "MSFT", "weight": "0.3100", "market_value": "31000"},
            {"instrument_id": 2, "symbol": "NVDA", "weight": "0.2100", "market_value": "21000"},
            {"instrument_id": 3, "symbol": "QUBT", "weight": "0.0400", "market_value": "4000"},
        ],
        "sector_exposures": [
            {
                "exposure_key": "TECHNOLOGY",
                "exposure_name": "Technology",
                "exposure_weight": "0.5600",
                "position_count": 2,
                "symbols": ["MSFT", "NVDA"],
            }
        ],
        "theme_exposures": [
            {
                "exposure_key": "AI_SEMICONDUCTOR_CYCLE",
                "exposure_name": "AI Semiconductor Cycle",
                "exposure_weight": "0.2100",
                "position_count": 1,
                "symbols": ["NVDA"],
            }
        ],
        "unclassified_weight": "0.0400",
        "unclassified_symbols": ["QUBT"],
    }


if __name__ == "__main__":
    unittest.main()
