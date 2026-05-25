from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import unittest

from stockanalysis.ai.cycle_community_ai_summary import (
    CODEX_OAUTH_PROVIDER,
    SUMMARY_TYPE,
    CycleCommunityAiProviderResponse,
    build_codex_oauth_cycle_community_ai_output_schema,
    build_codex_oauth_cycle_community_ai_prompt,
    parse_cycle_community_ai_response_payload,
    run_cycle_community_ai_summary_v2,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT_DIR / "db" / "migrations" / "0020_cycle_community_ai_summary_v2.sql"


class FakeCycleCommunityExecutor:
    def __init__(self, *, run_id: int = 9301) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.invocation_id = 8100

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- cycle graph context node code lookup"):
            return json.dumps(["MACRO_RATES_FED"])
        if sql.startswith("-- cycle graph context lookup"):
            return json.dumps(_context_payload())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.prompt_template" in sql:
            return "44"
        if "insert into ai.model_invocation" in sql:
            self.invocation_id += 1
            return str(self.invocation_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class CycleCommunityAiSummaryTests(unittest.TestCase):
    def test_migration_allows_ai_summary_type(self) -> None:
        sql = MIGRATION_PATH.read_text(encoding="utf-8")

        self.assertIn("drop constraint if exists cycle_community_summary_summary_type_check", sql)
        self.assertIn("'cycle_community_ai_v2'", sql)
        self.assertIn("idx_cycle_community_summary_type_node_date", sql)

    def test_prompt_and_schema_require_korean_cycle_fields(self) -> None:
        prompt = build_codex_oauth_cycle_community_ai_prompt(_context_payload(), max_context_chars=12000)
        schema = build_codex_oauth_cycle_community_ai_output_schema()
        summary_schema = schema["properties"]["summary"]

        self.assertIn("Write every human-readable field in Korean", prompt)
        self.assertIn("Do not browse", prompt)
        self.assertIn("watchlist_symbols", summary_schema["required"])
        self.assertIn("supporting_events", summary_schema["properties"])
        self.assertFalse(schema["properties"]["usage"]["additionalProperties"])
        self.assertIn("input_tokens", schema["properties"]["usage"]["properties"])

    def test_parse_filters_ungrounded_symbols_and_events(self) -> None:
        response = parse_cycle_community_ai_response_payload(
            {
                "provider": CODEX_OAUTH_PROVIDER,
                "model_name": "codex-test",
                "summary": {
                    "korean_summary": "금리 흐름이 기술주 리스크를 키우고 있다.",
                    "key_drivers": ["연준", "국채금리"],
                    "causal_paths": [{"path": ["MACRO_RATES_FED", "QQQ"], "explanation": "금리 부담", "confidence": 0.8}],
                    "supporting_events": [
                        {"event_id": 11, "title": "연준 금리 이슈가 계속 주목된다", "reason": "원천 뉴스"},
                        {"event_id": 999, "title": "없는 뉴스", "reason": "오염"},
                    ],
                    "conflicts": [],
                    "uncertainty": "다음 CPI 확인 필요",
                    "watchlist_symbols": ["QQQ", "XOM"],
                },
                "usage": {"input_tokens": 100, "output_tokens": 20},
            },
            context=_context_payload(),
        )

        self.assertEqual(response.provider, CODEX_OAUTH_PROVIDER)
        self.assertEqual(response.output.watchlist_symbols, ("QQQ",))
        self.assertEqual(len(response.output.supporting_events), 1)
        self.assertEqual(response.input_token_count, 100)

    def test_run_dry_run_builds_preview_without_writes(self) -> None:
        executor = FakeCycleCommunityExecutor()

        report = run_cycle_community_ai_summary_v2(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 24),
            provider="fixture",
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["summary_type"], SUMMARY_TYPE)
        self.assertEqual(report["node_count"], 1)
        self.assertIn("korean_summary", report["summary_preview"][0])
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_invocation_and_upserts_summary(self) -> None:
        executor = FakeCycleCommunityExecutor(run_id=9302)

        report = run_cycle_community_ai_summary_v2(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 24),
            node_codes=("MACRO_RATES_FED",),
            provider="fixture",
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9302)
        self.assertEqual(report["inserted_summary_count"], 1)
        self.assertTrue(any("insert into ai.model_invocation" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("insert into ai.cycle_community_summary" in sql for sql in executor.non_query_sql))
        self.assertIn(SUMMARY_TYPE, executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_execute_uses_fixture_fallback_when_provider_fails(self) -> None:
        executor = FakeCycleCommunityExecutor(run_id=9303)

        def failing_runner(
            context: dict[str, object],
            model_name: str,
            reasoning_effort: str | None,
            max_context_chars: int,
        ) -> CycleCommunityAiProviderResponse:
            raise RuntimeError("provider down")

        report = run_cycle_community_ai_summary_v2(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 24),
            node_codes=("MACRO_RATES_FED",),
            provider=CODEX_OAUTH_PROVIDER,
            execute=True,
            executor=executor,
            provider_runner=failing_runner,
        )

        self.assertEqual(report["status"], "completed_with_fallback")
        self.assertEqual(report["failed_summary_count"], 1)
        self.assertTrue(any("status = 'succeeded_with_fallback'" in sql for sql in executor.non_query_sql))
        self.assertTrue(any("provider down" in sql for sql in executor.scalar_sql))

    def test_run_dry_run_uses_selected_node_preview(self) -> None:
        report = run_cycle_community_ai_summary_v2(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 24),
            node_codes=("MACRO_RATES_FED",),
            provider="fixture",
            execute=False,
            executor=FakeCycleCommunityExecutor(),
        )
        self.assertEqual(report["node_code_preview"], ["MACRO_RATES_FED"])


def _context_payload() -> dict[str, object]:
    return {
        "query": {"node_code": "MACRO_RATES_FED", "as_of_date": "2026-05-24", "limit": 12},
        "target_node": {
            "node_id": 101,
            "code": "MACRO_RATES_FED",
            "name": "Macro Rates Fed",
            "node_type": "macro",
        },
        "latest_snapshot": {
            "cycle_level": "macro",
            "cycle_state": "risk_review",
            "cycle_score": "0.6200",
            "event_heat_score": "0.8100",
            "parent_alignment_score": "0.5700",
            "conflict_flags": ["growth_vs_rates"],
        },
        "parent_edges": [{"code": "MARKET_NEWS_FLOW", "relation_type": "hierarchy", "weight": "1.0"}],
        "child_edges": [{"code": "TECH_DOMAIN", "relation_type": "macro_to_domain", "weight": "0.75"}],
        "direct_events": [
            {
                "event_id": 11,
                "title": "Fed rates remain in focus",
                "korean_title": "연준 금리 이슈가 계속 주목된다",
                "impact_direction": "watch",
            }
        ],
        "propagated_impacts": [
            {"event_id": 11, "title": "Fed rates remain in focus", "primary_symbol": "QQQ"},
            {"event_id": 11, "title": "Fed rates remain in focus", "primary_symbol": "SPY"},
        ],
        "exposed_instruments": [
            {"primary_symbol": "SPY", "exposure_weight": "0.65"},
            {"primary_symbol": "QQQ", "exposure_weight": "0.75"},
        ],
        "ai_artifacts": [{"artifact_id": 291, "artifact_type": "news_event_candidate", "provider": "codex_oauth"}],
        "recommendations": [{"recommendation_id": 52, "primary_symbol": "QQQ", "action": "watch"}],
        "theses": [{"thesis_id": 7, "primary_symbol": "QQQ", "title": "AI cycle thesis"}],
        "previous_summary": None,
    }


if __name__ == "__main__":
    unittest.main()
