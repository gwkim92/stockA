from __future__ import annotations

import json
from datetime import date
import unittest

from stockanalysis.ai.equity_research_reporting import (
    ARTIFACT_TYPE,
    CODEX_OAUTH_PROVIDER,
    EquityResearchProviderResponse,
    build_codex_oauth_equity_research_output_schema,
    build_codex_oauth_equity_research_prompt,
    parse_equity_research_response_payload,
    render_equity_research_context_sql,
    render_equity_research_symbol_lookup_sql,
    run_equity_research_reporting,
)


class FakeEquityResearchExecutor:
    def __init__(self, *, run_id: int = 9701) -> None:
        self.run_id = run_id
        self.invocation_id = 8800
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- equity research symbol lookup"):
            return json.dumps(["NVDA"])
        if sql.startswith("-- equity research context lookup"):
            return json.dumps(_context_payload())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.prompt_template" in sql:
            return "44"
        if "insert into ai.model_invocation" in sql:
            self.invocation_id += 1
            return str(self.invocation_id)
        if "insert into research.equity_research_artifact" in sql:
            return "9901"
        raise AssertionError(f"Unexpected scalar SQL: {sql[:140]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EquityResearchReportingTests(unittest.TestCase):
    def test_context_sql_reads_professional_research_inputs_without_writes(self) -> None:
        sql = render_equity_research_context_sql(symbol="NVDA", as_of_date=date(2026, 5, 25))
        lowered = sql.lower()

        self.assertIn("-- equity research context lookup", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("market.peer_relative_snapshot", sql)
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("signal.recommendation_score_component", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("ai.cycle_community_summary", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_symbol_lookup_can_target_active_recommendations_or_explicit_symbols(self) -> None:
        implicit_sql = render_equity_research_symbol_lookup_sql(as_of_date=date(2026, 5, 25), limit=5)
        explicit_sql = render_equity_research_symbol_lookup_sql(
            as_of_date=date(2026, 5, 25),
            symbols=("nvda", "AAPL"),
            limit=5,
        )

        self.assertIn("signal.recommendation_batch", implicit_sql)
        self.assertIn("signal.recommendation recommendation", implicit_sql)
        self.assertIn("values ('NVDA'), ('AAPL')", explicit_sql)

    def test_prompt_and_schema_require_korean_professional_research_fields(self) -> None:
        prompt = build_codex_oauth_equity_research_prompt(_context_payload(), max_context_chars=16000)
        schema = build_codex_oauth_equity_research_output_schema()
        research_schema = schema["properties"]["research"]

        self.assertIn("Write every human-readable field in Korean", prompt)
        self.assertIn("Do not browse", prompt)
        self.assertIn("Do not change recommendation scores or weights", prompt)
        self.assertIn("usage", schema["required"])
        self.assertIn("valuation_sensitivity", research_schema["required"])
        self.assertFalse(research_schema["additionalProperties"])
        self.assertIn("cached_input_tokens", schema["properties"]["usage"]["required"])

    def test_parse_sanitizes_title_and_preserves_valid_sensitivity(self) -> None:
        response = parse_equity_research_response_payload(
            {
                "provider": CODEX_OAUTH_PROVIDER,
                "model_name": "codex-test",
                "research": {
                    "title": "기업 리서치",
                    "korean_summary": "재무와 밸류에이션을 함께 검토한다.",
                    "key_points": ["재무 품질 확인"],
                    "catalysts": ["AI 사이클"],
                    "risks": ["밸류에이션 부담"],
                    "invalidation_conditions": ["FCF 훼손"],
                    "valuation_sensitivity": {
                        "base_case": "기준",
                        "upside_case": "상단",
                        "downside_case": "하단",
                        "margin_of_safety_view": "제한적",
                        "confidence": 0.93,
                    },
                },
                "usage": {"input_tokens": 100, "output_tokens": 20, "cached_input_tokens": 50},
            },
            context=_context_payload(),
        )

        self.assertEqual(response.provider, CODEX_OAUTH_PROVIDER)
        self.assertTrue(response.output.title.startswith("NVDA"))
        self.assertEqual(response.output.valuation_sensitivity["confidence"], 0.93)
        self.assertEqual(response.input_token_count, 100)

    def test_run_dry_run_builds_preview_without_writes(self) -> None:
        executor = FakeEquityResearchExecutor()

        report = run_equity_research_reporting(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 25),
            provider="fixture",
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["artifact_type"], ARTIFACT_TYPE)
        self.assertEqual(report["symbol_preview"], ["NVDA"])
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_invocation_and_upserts_artifact(self) -> None:
        executor = FakeEquityResearchExecutor(run_id=9702)

        report = run_equity_research_reporting(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 25),
            symbols=("NVDA",),
            provider="fixture",
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9702)
        self.assertEqual(report["inserted_artifact_count"], 1)
        self.assertTrue(any("insert into ai.model_invocation" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("insert into research.equity_research_artifact" in sql for sql in executor.scalar_sql))
        artifact_sql = next(sql for sql in executor.scalar_sql if "insert into research.equity_research_artifact" in sql)
        self.assertIn("'full_equity_research'", artifact_sql)
        self.assertIn("'[7001]'", artifact_sql)
        self.assertTrue(any("status = 'succeeded'" in sql for sql in executor.non_query_sql))

    def test_run_execute_uses_fixture_fallback_when_provider_fails(self) -> None:
        executor = FakeEquityResearchExecutor(run_id=9703)

        def failing_runner(
            context: dict[str, object],
            model_name: str,
            reasoning_effort: str | None,
            max_context_chars: int,
        ) -> EquityResearchProviderResponse:
            raise RuntimeError("provider down")

        report = run_equity_research_reporting(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 25),
            symbols=("NVDA",),
            provider=CODEX_OAUTH_PROVIDER,
            execute=True,
            executor=executor,
            provider_runner=failing_runner,
        )

        self.assertEqual(report["status"], "completed_with_fallback")
        self.assertEqual(report["failed_artifact_count"], 1)
        self.assertTrue(any("provider down" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("status = 'succeeded_with_fallback'" in sql for sql in executor.non_query_sql))


def _context_payload() -> dict[str, object]:
    return {
        "query": {"symbol": "NVDA", "as_of_date": "2026-05-25", "limit": 8},
        "instrument": {
            "instrument_id": 501,
            "primary_symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "market_code": "US",
            "currency_code": "USD",
        },
        "financial_metrics": [
            {"metric_code": "net_margin", "metric_value": "0.5200", "metric_status": "computed", "period_end": "2026-04-26"},
            {"metric_code": "free_cash_flow_margin", "metric_value": "0.4100", "metric_status": "computed", "period_end": "2026-04-26"},
            {"metric_code": "leverage_ratio", "metric_value": "0.1200", "metric_status": "computed", "period_end": "2026-04-26"},
        ],
        "financial_metric_status_counts": [{"metric_status": "computed", "metric_count": 3}],
        "peer_relative": [
            {
                "peer_group_code": "US_CORE_FINANCIAL_DISCLOSURE",
                "metric_code": "net_margin",
                "percentile_rank": "0.9000",
                "relative_signal": "top_quartile",
            }
        ],
        "valuations": [
            {
                "method": "dcf_lite",
                "base_price": "120.00",
                "fair_value_low": "100.00",
                "fair_value_base": "135.00",
                "fair_value_high": "160.00",
                "margin_of_safety": "0.1250",
                "confidence": "0.4500",
            }
        ],
        "recommendation": {
            "recommendation_id": 140,
            "as_of_date": "2026-05-23",
            "action": "monitor_or_accumulate",
            "total_score": "0.6200",
            "thesis_id": 5,
        },
        "fundamental_components": [
            {"component_name": "fundamental_quality_score", "component_score": "0.6750", "component_weight": "0.0000"},
            {"component_name": "valuation_margin_score", "component_score": "0.3990", "component_weight": "0.0000"},
        ],
        "thesis": {
            "thesis_id": 5,
            "title": "NVDA AI cycle thesis",
            "summary": "AI accelerator demand supports the thesis.",
            "status": "active",
            "invalidation_conditions": "FCF margin degradation or AI cycle demand break.",
        },
        "recent_events": [
            {
                "event_id": 9001,
                "title": "Nvidia venture investments expand",
                "korean_title": "Nvidia 벤처 투자가 확대된다",
                "impact_direction": "watch",
                "document_id": 7001,
            }
        ],
        "cycle_summaries": [
            {
                "node_code": "AI_SEMICONDUCTOR_CYCLE",
                "summary_json": {"korean_summary": "AI 반도체 사이클은 확산 중이다."},
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
