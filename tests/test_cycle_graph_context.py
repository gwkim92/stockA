from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import unittest

from stockanalysis.ai.cycle_graph_context import (
    SUMMARY_TYPE,
    build_cycle_community_summary,
    load_cycle_graph_context,
    load_cycle_graph_context_node_codes,
    render_cycle_community_summary_upsert_sql,
    render_cycle_graph_context_node_codes_sql,
    render_cycle_graph_context_sql,
    run_cycle_graph_context_summary,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT_DIR / "db" / "migrations" / "0019_cycle_graph_context_summary.sql"


class FakeExecutor:
    def __init__(self, *, run_id: int = 9201, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- cycle graph context node code lookup"):
            return json.dumps(["MACRO_RATES_FED", "TECH_DOMAIN"])
        if sql.startswith("-- cycle graph context lookup"):
            if "TECH_DOMAIN" in sql:
                return json.dumps(_context_payload(node_id=201, node_code="TECH_DOMAIN", node_type="domain"))
            return json.dumps(_context_payload(node_id=101, node_code="MACRO_RATES_FED", node_type="subtheme"))
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into ai.cycle_community_summary" in sql:
            raise RuntimeError("boom")


class MissingNodeExecutor:
    def execute_scalar(self, sql: str) -> str:
        return json.dumps({"target_node": None})


class CycleGraphContextTests(unittest.TestCase):
    def test_migration_creates_cycle_community_summary(self) -> None:
        sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()

        self.assertIn("create table if not exists ai.cycle_community_summary", sql)
        self.assertIn("summary_json jsonb not null", sql)
        self.assertIn("source_run_id bigint references ops.pipeline_run", sql)
        self.assertIn("primary key (node_id, as_of_date, summary_type)", sql)

    def test_render_cycle_graph_context_sql_is_read_only_and_bounded(self) -> None:
        sql = render_cycle_graph_context_sql(node_code="macro_rates_fed", as_of_date=date(2026, 5, 23), limit=7)
        lowered = sql.lower()

        self.assertIn("'MACRO_RATES_FED'", sql)
        self.assertIn("'2026-05-23'::date", sql)
        self.assertIn("signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("signal.hierarchical_propagated_instrument_impact", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("signal.recommendation", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("ai.cycle_community_summary", sql)
        self.assertIn("limit 7", lowered)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_render_cycle_graph_context_sql_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            render_cycle_graph_context_sql(node_code="", as_of_date=date(2026, 5, 23))
        with self.assertRaises(ValueError):
            render_cycle_graph_context_sql(node_code="TECH_DOMAIN", as_of_date=date(2026, 5, 23), limit=0)

    def test_render_node_codes_sql_uses_latest_v2_snapshot(self) -> None:
        sql = render_cycle_graph_context_node_codes_sql(as_of_date=date(2026, 5, 23), limit=17)

        self.assertIn("signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("node.taxonomy_family = 'internal_theme'", sql)
        self.assertIn("node.code <> 'MARKET_NEWS_FLOW'", sql)
        self.assertIn("limit 17", sql.lower())

    def test_load_context_and_node_codes(self) -> None:
        executor = FakeExecutor()

        codes = load_cycle_graph_context_node_codes(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            executor=executor,
        )
        context = load_cycle_graph_context(
            config=type("Config", (), {})(),
            node_code="MACRO_RATES_FED",
            as_of_date=date(2026, 5, 23),
            executor=executor,
        )

        self.assertEqual(codes, ("MACRO_RATES_FED", "TECH_DOMAIN"))
        self.assertEqual(context["target_node"]["code"], "MACRO_RATES_FED")

    def test_load_context_rejects_missing_node(self) -> None:
        with self.assertRaises(ValueError):
            load_cycle_graph_context(
                config=type("Config", (), {})(),
                node_code="MISSING",
                as_of_date=date(2026, 5, 23),
                executor=MissingNodeExecutor(),
            )

    def test_build_summary_counts_and_korean_text(self) -> None:
        summary = build_cycle_community_summary(_context_payload(node_id=101, node_code="MACRO_RATES_FED", node_type="subtheme"))

        self.assertEqual(summary.node_id, 101)
        self.assertEqual(summary.node_code, "MACRO_RATES_FED")
        self.assertEqual(summary.summary_json["summary_type"], SUMMARY_TYPE)
        self.assertEqual(summary.summary_json["cycle_level"], "macro")
        self.assertEqual(summary.summary_json["counts"]["direct_event_count"], 1)
        self.assertEqual(summary.summary_json["counts"]["propagated_impact_count"], 2)
        self.assertIn("QQQ", summary.summary_json["top_symbols"])
        self.assertIn("최근 직접 뉴스 1건", summary.summary_json["summary_text_ko"])
        self.assertFalse(summary.summary_json["llm_used"])

    def test_render_summary_upsert_sql(self) -> None:
        summary = build_cycle_community_summary(_context_payload(node_id=101, node_code="MACRO_RATES_FED", node_type="subtheme"))

        sql = render_cycle_community_summary_upsert_sql(
            (summary,),
            as_of_date=date(2026, 5, 23),
            source_run_id=77,
        )

        self.assertIn("insert into ai.cycle_community_summary", sql)
        self.assertIn("on conflict (node_id, as_of_date, summary_type) do update", sql)
        self.assertIn("cycle_graph_context_v1", sql)
        self.assertIn("77::bigint", sql)

    def test_run_dry_run_loads_all_nodes_without_writes(self) -> None:
        executor = FakeExecutor()

        report = run_cycle_graph_context_summary(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(report["node_code_preview"], ["MACRO_RATES_FED", "TECH_DOMAIN"])
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_run_and_writes_summary(self) -> None:
        executor = FakeExecutor(run_id=9202)

        report = run_cycle_graph_context_summary(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 23),
            node_codes=("MACRO_RATES_FED",),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9202)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ai.cycle_community_summary", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_execute_marks_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=9203, fail_on_upsert=True)

        with self.assertRaises(RuntimeError):
            run_cycle_graph_context_summary(
                config=type("Config", (), {})(),
                as_of_date=date(2026, 5, 23),
                node_codes=("MACRO_RATES_FED",),
                execute=True,
                executor=executor,
            )

        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _context_payload(*, node_id: int, node_code: str, node_type: str) -> dict[str, object]:
    return {
        "query": {"node_code": node_code, "as_of_date": "2026-05-23", "limit": 12},
        "target_node": {
            "node_id": node_id,
            "code": node_code,
            "name": node_code.replace("_", " ").title(),
            "node_type": node_type,
        },
        "latest_snapshot": {
            "cycle_level": "macro" if node_code.startswith("MACRO_") else "domain",
            "cycle_state": "neutral",
            "cycle_score": "0.5140",
            "event_heat_score": "0.5000",
            "parent_alignment_score": "0.4977",
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
