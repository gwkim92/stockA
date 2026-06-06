from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.cycle_ai_quality_audit import (
    load_cycle_ai_quality_audit_visibility_report,
    render_duplicate_title_cleanup_sql,
    render_cycle_ai_quality_audit_sql,
    render_stale_direct_impact_cleanup_sql,
    run_duplicate_title_cleanup,
    run_cycle_ai_quality_audit,
    run_stale_direct_impact_cleanup,
)


class FakeExecutor:
    def __init__(self, state: dict[str, object]) -> None:
        self.state = state
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- cycle ai quality audit lookup"):
            return json.dumps(self.state)
        if sql.startswith("-- cycle ai stale direct impact cleanup"):
            execute = "'execute', true" in sql
            return json.dumps(
                {
                    "as_of_date": "2026-05-24",
                    "lookback_days": 30,
                    "execute": execute,
                    "candidate_count": 1,
                    "removed_count": 1 if execute else 0,
                    "samples": [
                        {
                            "event_id": 19,
                            "symbol": "SPY",
                            "instrument_name": "SPDR S&P 500 ETF TRUST",
                            "event_title": "Dow Jones Futures Rise But Pare Gains",
                        }
                    ],
                }
            )
        if sql.startswith("-- cycle ai duplicate title cleanup"):
            execute = "'execute', true" in sql
            return json.dumps(
                {
                    "as_of_date": "2026-05-24",
                    "lookback_days": 30,
                    "execute": execute,
                    "candidate_count": 1,
                    "merged_classification_count": 1 if execute else 0,
                    "deleted_conflicting_classification_count": 1 if execute else 0,
                    "merged_propagated_count": 2 if execute else 0,
                    "deleted_conflicting_propagated_count": 2 if execute else 0,
                    "merged_hierarchical_count": 3 if execute else 0,
                    "deleted_conflicting_hierarchical_count": 2 if execute else 0,
                    "merged_chunk_count": 1 if execute else 0,
                    "merged_artifact_count": 1 if execute else 0,
                    "deleted_event_count": 1 if execute else 0,
                    "deleted_document_count": 1 if execute else 0,
                    "samples": [
                        {
                            "event_id": 881,
                            "document_id": 896,
                            "keeper_event_id": 880,
                            "keeper_document_id": 895,
                            "title": "SpaceX's road to landmark IPO filing",
                            "duplicate_group_count": 2,
                            "duplicate_rank": 2,
                        }
                    ],
                }
            )
        if sql.startswith("insert into ops.pipeline_run"):
            return "9401"
        raise AssertionError(f"Unexpected scalar SQL: {sql[:80]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class CycleAiQualityAuditTests(unittest.TestCase):
    def test_render_sql_checks_contamination_and_quality_layers(self) -> None:
        sql = render_cycle_ai_quality_audit_sql(as_of_date=date(2026, 5, 24), lookback_days=14)

        self.assertTrue(sql.startswith("-- cycle ai quality audit lookup"))
        self.assertIn("quantum_energy_mislinks", sql)
        self.assertIn("ungrounded_direct_tickers", sql)
        self.assertIn("source_aliases(primary_symbol, alias_text)", sql)
        self.assertIn("('SPY', 's&p 500')", sql)
        self.assertIn("('QQQ', 'nasdaq')", sql)
        self.assertIn("regexp_split_to_table(instrument.name", sql)
        self.assertIn("normal_macro_flows", sql)
        self.assertIn("cross_theme_mismatch_rules", sql)
        self.assertIn("cross_theme_mismatches", sql)
        self.assertIn("duplicate_flow_evidence", sql)
        self.assertIn("weak_propagation_evidence", sql)
        self.assertIn("'macro_false_tickers'", sql)
        self.assertIn("'normal_macro_flows'", sql)
        self.assertIn("'cross_theme_mismatch_count'", sql)
        self.assertIn("'duplicate_flow_evidence_count'", sql)
        self.assertIn("'weak_propagation_evidence_count'", sql)
        self.assertIn("'cross_theme_mismatches'", sql)
        self.assertIn("'duplicate_flow_evidence'", sql)
        self.assertIn("'weak_propagation_evidence'", sql)
        self.assertIn("'event_title'", sql)
        self.assertIn("'node_codes'", sql)
        self.assertIn("path_weight", sql)
        self.assertIn("source_document_count", sql)
        self.assertIn("signal.hierarchical_propagated_instrument_impact", sql)
        self.assertIn("signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("trading.paper_validation_run", sql)
        self.assertIn("'readiness_gaps'", sql)
        self.assertIn("'cycle_snapshot_missing'", sql)
        self.assertIn("'hierarchical_impact_missing'", sql)

    def test_run_dry_run_returns_secret_free_report_without_pipeline_write(self) -> None:
        executor = FakeExecutor(_sample_state())

        report = run_cycle_ai_quality_audit(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            lookback_days=30,
            execute=False,
            executor=executor,
            generated_at=datetime(2026, 5, 24, tzinfo=timezone.utc),
        )

        self.assertEqual(report["report_name"], "cycle_ai_quality_audit")
        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["audit_status"], "attention_required")
        self.assertEqual(report["issue_count"], 2)
        self.assertEqual(report["readiness_gaps"], [])
        self.assertIn("normal_macro_flows", report["samples"])
        self.assertIn("macro_false_tickers", report["samples"])
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_report_includes_hardened_audit_next_actions(self) -> None:
        executor = FakeExecutor(
            _sample_state(
                issue_count=3,
                checks={
                    "cross_theme_mismatch_count": 1,
                    "duplicate_flow_evidence_count": 1,
                    "weak_propagation_evidence_count": 1,
                },
                samples={
                    "cross_theme_mismatches": [
                        {
                            "event_id": 11,
                            "node_code": "ENERGY_GEOPOLITICS",
                            "rule_key": "rates_news_on_energy_geopolitics",
                            "label": "금리·연준 뉴스가 에너지 지정학 흐름으로 연결됨",
                            "event_title": "Fed rate cut odds rise",
                        }
                    ],
                    "duplicate_flow_evidence": [
                        {
                            "title": "same news",
                            "event_count": 2,
                            "node_count": 2,
                            "node_codes": ["MACRO_RATES_FED", "TECH_DOMAIN"],
                        }
                    ],
                    "weak_propagation_evidence": [
                        {
                            "event_id": 12,
                            "source_node_code": "MACRO_RATES_FED",
                            "propagated_node_code": "TECH_DOMAIN",
                            "symbol": "QQQ",
                            "confidence": 0.2,
                            "path_weight": 0.08,
                        }
                    ],
                },
            )
        )

        report = run_cycle_ai_quality_audit(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["checks"]["cross_theme_mismatch_count"], 1)
        self.assertEqual(report["checks"]["duplicate_flow_evidence_count"], 1)
        self.assertEqual(report["checks"]["weak_propagation_evidence_count"], 1)
        self.assertIn("cross_theme_mismatches", report["samples"])
        self.assertIn("duplicate_flow_evidence", report["samples"])
        self.assertIn("weak_propagation_evidence", report["samples"])
        self.assertIn(
            "inspect cross-theme news mismatches before using cycle evidence",
            report["next_actions"],
        )
        self.assertIn(
            "merge duplicate news flow evidence before cycle review",
            report["next_actions"],
        )
        self.assertIn(
            "review weak cycle propagation evidence before recommendation input",
            report["next_actions"],
        )

    def test_run_execute_records_pipeline_run(self) -> None:
        executor = FakeExecutor(_sample_state(audit_status="ok", issue_count=0))

        report = run_cycle_ai_quality_audit(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9401)
        self.assertTrue(any("pipeline_name" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("update ops.pipeline_run" in sql for sql in executor.non_query_sql))

    def test_visibility_report_sanitizes_repo_outside_summary(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            report_path = Path(outside_root) / "cycle-ai-quality-audit.json"
            report_path.write_text(
                json.dumps(
                    {
                        "report_name": "cycle_ai_quality_audit",
                        "generated_at": "2026-05-24T00:00:00Z",
                        "execute": True,
                        "as_of_date": "2026-05-24",
                        "lookback_days": 30,
                        "audit_status": "ok",
                        "audit_score": 100,
                        "issue_count": 0,
                        "readiness_gap_count": 1,
                        "readiness_gaps": [
                            {
                                "gap_key": "cycle_snapshot_missing",
                                "label": "사이클 스냅샷 결과 없음",
                                "metric_key": "cycle_snapshot_count",
                                "current_value": 0,
                                "next_action": "run decision-daily or cycle-hierarchy-snapshot-v2-run",
                            }
                        ],
                        "metrics": {"rss_document_count": 10, "translated_document_count": 10},
                        "checks": {"quantum_energy_mislink_count": 0},
                        "samples": {},
                        "next_actions": ["continue scheduled runs"],
                    }
                ),
                encoding="utf-8",
            )

            visibility = load_cycle_ai_quality_audit_visibility_report(
                report_path=report_path,
                repo_root=repo_root,
            )

        self.assertEqual(visibility["status"], "ok")
        self.assertEqual(visibility["audit_score"], 100)
        self.assertEqual(visibility["metrics"]["rss_document_count"], 10)
        self.assertEqual(visibility["readiness_gap_count"], 1)
        self.assertEqual(visibility["readiness_gaps"][0]["gap_key"], "cycle_snapshot_missing")
        self.assertEqual(visibility["source"], "cycle_ai_quality_audit_report")

    def test_render_stale_direct_impact_cleanup_sql_previews_without_delete(self) -> None:
        sql = render_stale_direct_impact_cleanup_sql(
            as_of_date=date(2026, 5, 24),
            lookback_days=30,
            execute=False,
            limit=25,
        )

        self.assertTrue(sql.startswith("-- cycle ai stale direct impact cleanup"))
        self.assertIn("event_row.event_type = 'news_rss_item'", sql)
        self.assertIn("source_aliases(primary_symbol, alias_text)", sql)
        self.assertIn("stale_direct_impacts as", sql)
        self.assertNotIn("delete from event.event_instrument_impact", sql)
        self.assertIn("'removed_count'", sql)

    def test_render_stale_direct_impact_cleanup_sql_execute_deletes_only_stale_direct_impacts(self) -> None:
        sql = render_stale_direct_impact_cleanup_sql(
            as_of_date=date(2026, 5, 24),
            execute=True,
        )

        self.assertIn("delete from event.event_instrument_impact impact", sql)
        self.assertIn("using stale_direct_impacts stale", sql)
        self.assertIn("impact.event_id = stale.event_id", sql)
        self.assertIn("impact.instrument_id = stale.instrument_id", sql)

    def test_run_stale_direct_impact_cleanup_preview_is_secret_free_and_does_not_write_pipeline(self) -> None:
        executor = FakeExecutor(_sample_state())

        report = run_stale_direct_impact_cleanup(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["report_name"], "cycle_ai_stale_direct_impact_cleanup")
        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["removed_count"], 0)
        self.assertEqual(executor.non_query_sql, [])
        self.assertFalse(any(sql.startswith("insert into ops.pipeline_run") for sql in executor.scalar_sql))

    def test_run_stale_direct_impact_cleanup_execute_records_pipeline_run(self) -> None:
        executor = FakeExecutor(_sample_state())

        report = run_stale_direct_impact_cleanup(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9401)
        self.assertEqual(report["removed_count"], 1)
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertTrue(any("update ops.pipeline_run" in sql for sql in executor.non_query_sql))

    def test_render_duplicate_title_cleanup_sql_previews_safe_duplicate_events_only(self) -> None:
        sql = render_duplicate_title_cleanup_sql(
            as_of_date=date(2026, 5, 24),
            lookback_days=30,
            execute=False,
            limit=25,
        )

        self.assertTrue(sql.startswith("-- cycle ai duplicate title cleanup"))
        self.assertIn("duplicate_group_count > 1", sql)
        self.assertIn("keeper_event_id", sql)
        self.assertIn("partition by document.normalized_title, document.observed_at", sql)
        self.assertIn("finance.yahoo.com", sql)
        self.assertIn("merged_artifacts as", sql)
        self.assertIn("deleted_conflicting_classification as", sql)
        self.assertIn("deleted_conflicting_propagated as", sql)
        self.assertIn("deleted_conflicting_hierarchical as", sql)
        self.assertNotIn("delete from event.event event_row", sql)

    def test_render_duplicate_title_cleanup_sql_execute_deletes_events_and_documents(self) -> None:
        sql = render_duplicate_title_cleanup_sql(as_of_date=date(2026, 5, 24), execute=True)

        self.assertIn("delete from event.event event_row", sql)
        self.assertIn("delete from ingest.source_document document", sql)
        self.assertIn("using cleanup_candidates candidate", sql)
        self.assertIn("update ai.extraction_artifact artifact", sql)
        self.assertIn("update ai.document_chunk chunk", sql)

    def test_run_duplicate_title_cleanup_preview_is_secret_free_and_does_not_write_pipeline(self) -> None:
        executor = FakeExecutor(_sample_state())

        report = run_duplicate_title_cleanup(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            execute=False,
            executor=executor,
        )

        self.assertEqual(report["report_name"], "cycle_ai_duplicate_title_cleanup")
        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["candidate_count"], 1)
        self.assertEqual(report["deleted_event_count"], 0)
        self.assertEqual(report["deleted_document_count"], 0)
        self.assertFalse(any(sql.startswith("insert into ops.pipeline_run") for sql in executor.scalar_sql))

    def test_run_duplicate_title_cleanup_execute_records_pipeline_run(self) -> None:
        executor = FakeExecutor(_sample_state())

        report = run_duplicate_title_cleanup(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9401)
        self.assertEqual(report["deleted_event_count"], 1)
        self.assertEqual(report["deleted_document_count"], 1)
        self.assertEqual(report["merged_artifact_count"], 1)
        self.assertEqual(report["merged_classification_count"], 1)
        self.assertEqual(report["deleted_conflicting_classification_count"], 1)
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertTrue(any("update ops.pipeline_run" in sql for sql in executor.non_query_sql))


def _sample_state(
    *,
    audit_status: str = "attention_required",
    issue_count: int = 2,
    checks: dict[str, object] | None = None,
    samples: dict[str, object] | None = None,
) -> dict[str, object]:
    base_checks: dict[str, object] = {
        "duplicate_title_count": 1,
        "ungrounded_direct_ticker_count": 1,
        "macro_false_ticker_count": 0,
        "quantum_energy_mislink_count": 0,
        "cross_theme_mismatch_count": 0,
        "duplicate_flow_evidence_count": 0,
        "weak_propagation_evidence_count": 0,
        "normal_macro_flow_count": 4,
    }
    if checks is not None:
        base_checks.update(checks)
    base_samples: dict[str, object] = {
        "ungrounded_direct_tickers": [{"event_id": 1, "symbol": "SPY", "event_title": "Fed news"}],
        "macro_false_tickers": [
            {
                "event_id": 2,
                "symbol": "QQQ",
                "instrument_name": "Invesco QQQ Trust",
                "event_title": "Fed holds rates",
                "node_codes": ["MACRO_RATES_FED"],
                "impact_direction": "risk_review",
            }
        ],
        "normal_macro_flows": [
            {
                "event_id": 3,
                "event_title": "Inflation cools",
                "node_codes": ["MACRO_INFLATION"],
                "impact_directions": ["supportive"],
            }
        ],
    }
    if samples is not None:
        base_samples.update(samples)
    return {
        "as_of_date": "2026-05-24",
        "lookback_days": 30,
        "audit_status": audit_status,
        "audit_score": 70,
        "issue_count": issue_count,
        "readiness_gap_count": 0,
        "metrics": {
            "rss_document_count": 12,
            "translated_document_count": 10,
            "accepted_artifact_count": 3,
            "rejected_artifact_count": 1,
            "codex_succeeded_count": 3,
            "hierarchical_impact_count": 20,
            "cycle_snapshot_count": 8,
            "recommendation_cycle_component_count": 30,
            "paper_validation_count": 1,
            "paper_validation_passed_count": 1,
        },
        "checks": base_checks,
        "samples": base_samples,
    }


if __name__ == "__main__":
    unittest.main()
