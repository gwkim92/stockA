from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.professional_source_gap_remediation_decision import (
    build_professional_source_gap_remediation_decision,
    render_professional_source_gap_remediation_decision_insert_sql,
    run_professional_source_gap_remediation_decision,
)


class FakeSourceGapDecisionExecutor:
    def __init__(self, *, source_gap_payload: dict[str, object], run_id: int = 9901, eval_run_id: int = 7701) -> None:
        self.source_gap_payload = source_gap_payload
        self.run_id = run_id
        self.eval_run_id = eval_run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return str(self.run_id)
        if "insert into ai.eval_run" in lowered:
            return str(self.eval_run_id)
        return json.dumps(
            {
                "overall_status": "attention_required",
                "professional_source_gap_prioritization": self.source_gap_payload,
            }
        )

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class ProfessionalSourceGapRemediationDecisionTests(unittest.TestCase):
    def test_classifies_source_blocker_and_selects_next_deterministic_gap(self) -> None:
        decision = build_professional_source_gap_remediation_decision(
            _source_gap_payload(),
            as_of_date=date(2026, 5, 26),
        )

        self.assertEqual(decision["decision_status"], "next_deterministic_remediation_available")
        top_gap = decision["top_gap_decision"]
        self.assertEqual(top_gap["symbol"], "EROK")
        self.assertEqual(top_gap["decision_type"], "non_remediable_current_free_public_data")
        self.assertFalse(top_gap["remediation_allowed"])
        self.assertEqual(top_gap["future_task"], "raw_filing_xbrl_or_alternate_public_filing_parser")
        next_gap = decision["next_remediable_gap"]
        self.assertEqual(next_gap["symbol"], "GOOG")
        self.assertEqual(next_gap["decision_type"], "deterministic_remediation_available")
        self.assertIn("sum-of-parts-valuation-run", next_gap["remediation_command"])
        self.assertIn("--as-of-date 2026-05-26", next_gap["remediation_command"])
        spy = [item for item in decision["decisions"] if item["symbol"] == "SPY"][0]
        self.assertEqual(spy["decision_type"], "fund_not_applicable")
        self.assertFalse(decision["guardrails"]["recommendation_scoring_mutated"])
        self.assertFalse(decision["guardrails"]["automatic_order_allowed"])
        self.assertEqual(decision["guardrails"]["order_boundary"], "read_only_no_order")

    def test_render_insert_records_ai_eval_run_without_weight_or_order_changes(self) -> None:
        sql = render_professional_source_gap_remediation_decision_insert_sql(
            score_json={
                "decision_status": "next_deterministic_remediation_available",
                "guardrails": {
                    "recommendation_scoring_mutated": False,
                    "automatic_order_allowed": False,
                },
            }
        )

        self.assertIn("insert into ai.eval_run", sql)
        self.assertIn("professional_source_gap_remediation_decision", sql)
        self.assertIn("professional-source-gap-remediation-decision-v1", sql)
        self.assertIn("recommendation_scoring_mutated", sql)
        self.assertNotIn("update signal.recommendation", sql.lower())
        self.assertNotIn("broker", sql.lower().split("score_json")[0])

    def test_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeSourceGapDecisionExecutor(source_gap_payload=_source_gap_payload(), run_id=9902, eval_run_id=7702)

        report = run_professional_source_gap_remediation_decision(
            config=RuntimeConfig(psql_command="docker exec psql"),
            as_of_date=date(2026, 5, 26),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9902)
        self.assertEqual(report["eval_run_id"], 7702)
        self.assertEqual(report["decision"]["top_gap_decision"]["symbol"], "EROK")
        self.assertEqual(report["decision"]["next_remediable_gap"]["symbol"], "GOOG")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _source_gap_payload() -> dict[str, object]:
    return {
        "status": "source_blockers_present",
        "as_of_date": "2026-05-26",
        "gap_count": 3,
        "source_blocker_count": 1,
        "coverage_gap_count": 1,
        "fund_not_applicable_count": 1,
        "gaps": [
            {
                "priority_rank": 1,
                "symbol": "EROK",
                "instrument_id": "instrument-3012",
                "instrument_name": "EagleRock Land, LLC",
                "product_type": "operating_company",
                "gap_status": "source_blockers_present",
                "priority_band": "high",
                "priority_score": 93.486,
                "missing_layers": [
                    "financial_metric_normalized",
                    "peer_relative_snapshot",
                    "segment_footnote_evidence",
                    "sum_of_parts_component",
                    "valuation_snapshot",
                    "industry_competitive_position",
                ],
                "blocker_type": "source_blocker",
                "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
            },
            {
                "priority_rank": 2,
                "symbol": "GOOG",
                "instrument_id": "instrument-5961",
                "instrument_name": "Alphabet Inc.",
                "product_type": "operating_company",
                "gap_status": "coverage_gaps_present",
                "priority_band": "medium",
                "priority_score": 19.876,
                "missing_layers": ["sum_of_parts_component"],
                "blocker_type": "coverage_gap",
                "blocker_code": "",
            },
            {
                "priority_rank": 3,
                "symbol": "SPY",
                "instrument_id": "instrument-5832",
                "instrument_name": "SPDR S&P 500 ETF TRUST",
                "product_type": "fund_or_etf",
                "gap_status": "fund_company_model_not_applicable",
                "priority_band": "watch",
                "priority_score": 31.309,
                "missing_layers": [],
                "blocker_type": "fund_not_applicable",
                "blocker_code": "fund_company_financial_model_not_applicable",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
