from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.news.cluster_evidence import (
    build_news_rss_clusters,
    load_news_rss_cluster_evidence_events,
    run_news_rss_cluster_evidence,
)
from stockanalysis.ingest.news.models import NewsRssClusterEvidenceEvent
from stockanalysis.ingest.news.sql import (
    render_existing_news_rss_cluster_artifact_lookup_sql,
    render_news_rss_cluster_evidence_event_candidates_sql,
    render_news_rss_cluster_extraction_artifact_insert_sql,
    render_news_rss_cluster_model_invocation_insert_sql,
)
from stockanalysis.ingest.psql import PsqlExecutionError


class FakeExecutor:
    def __init__(self, *, existing_artifact_id: int | None = None) -> None:
        self.existing_artifact_id = existing_artifact_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.next_invocation_id = 8101
        self.next_artifact_id = 9101
        self.events = [
            {
                "event_id": 101,
                "document_id": 501,
                "event_type": "news_rss_item",
                "title": "Nvidia H200 China deal survived the summit",
                "summary": "GPU export path stays open.",
                "event_at": "2026-05-19T10:02:40+00:00",
                "source_name": "rss_news:ai-semiconductor-cycle",
                "external_document_id": "rss:ai-semiconductor-cycle:abc",
                "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                "theme_name": "AI Semiconductor Cycle",
                "impact_direction": "supportive",
                "impact_score": 0.66,
                "symbol": "NVDA",
            },
            {
                "event_id": 102,
                "document_id": 502,
                "event_type": "news_rss_item",
                "title": "AI infrastructure demand strains legacy platforms",
                "summary": "Compute demand remains high.",
                "event_at": "2026-05-19T09:30:00+00:00",
                "source_name": "rss_news:ai-semiconductor-cycle",
                "external_document_id": "rss:ai-semiconductor-cycle:def",
                "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                "theme_name": "AI Semiconductor Cycle",
                "impact_direction": "watch",
                "impact_score": 0.55,
                "symbol": None,
            },
            {
                "event_id": 103,
                "document_id": 503,
                "event_type": "news_rss_item",
                "title": "Treasury sell-off eases as Fed credibility is tested",
                "summary": "Sticky prices keep rates in focus.",
                "event_at": "2026-05-19T09:10:00+00:00",
                "source_name": "rss_news:macro-rates-fed",
                "external_document_id": "rss:macro-rates-fed:abc",
                "theme_key": "MACRO_RATES_FED",
                "theme_name": "Macro Rates and Fed",
                "impact_direction": "risk_review",
                "impact_score": 0.68,
                "symbol": None,
            },
        ]

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from event.event e" in sql:
            return json.dumps(self.events)
        if "from ai.extraction_artifact artifact" in sql:
            if self.existing_artifact_id is None:
                raise PsqlExecutionError("psql returned no rows for scalar query")
            return str(self.existing_artifact_id)
        if "insert into ops.pipeline_run" in sql:
            return "7001"
        if "insert into ai.model_invocation" in sql:
            invocation_id = self.next_invocation_id
            self.next_invocation_id += 1
            return str(invocation_id)
        if "insert into ai.extraction_artifact" in sql:
            artifact_id = self.next_artifact_id
            self.next_artifact_id += 1
            return str(artifact_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class NewsRssClusterEvidenceTests(unittest.TestCase):
    def test_render_cluster_event_candidates_sql(self) -> None:
        sql = render_news_rss_cluster_evidence_event_candidates_sql(as_of_date=date(2026, 5, 19), limit=25)

        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("join lateral", sql)
        self.assertIn("classification_impact.confidence desc nulls last", sql)
        self.assertIn("instrument_impact.confidence desc nulls last", sql)
        self.assertIn("e.event_type = 'news_rss_item'", sql)
        self.assertIn("2026-05-19", sql)
        self.assertIn("limit 25", sql)
        self.assertNotIn("join event.event_classification_impact classification_impact\n      on", sql)
        self.assertNotIn("left join event.event_instrument_impact instrument_impact\n      on", sql)

    def test_render_existing_artifact_lookup_uses_request_hash(self) -> None:
        sql = render_existing_news_rss_cluster_artifact_lookup_sql(request_hash="abc")

        self.assertIn("artifact.artifact_type = 'news_cluster_summary'", sql)
        self.assertIn("invocation.request_hash = 'abc'", sql)

    def test_render_model_invocation_records_zero_cost_local_provider(self) -> None:
        sql = render_news_rss_cluster_model_invocation_insert_sql(run_id=7, request_hash="abc")

        self.assertIn("'local_rules'", sql)
        self.assertIn("'news_cluster_summary_v1'", sql)
        self.assertIn("0.000000", sql)

    def test_render_artifact_insert_attaches_representative_event(self) -> None:
        sql = render_news_rss_cluster_extraction_artifact_insert_sql(
            invocation_id=9,
            document_id=11,
            event_id=13,
            output_json='{"ok": true}',
            confidence=0.81,
        )

        self.assertIn("'news_cluster_summary'", sql)
        self.assertIn("11::bigint", sql)
        self.assertIn("13", sql)

    def test_load_news_rss_cluster_evidence_events(self) -> None:
        executor = FakeExecutor()
        events = load_news_rss_cluster_evidence_events(
            as_of_date=date(2026, 5, 19),
            limit=10,
            executor=executor,
        )

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_id, 101)
        self.assertEqual(events[0].symbol, "NVDA")

    def test_build_news_rss_clusters_groups_by_theme_and_symbols(self) -> None:
        events = (
            NewsRssClusterEvidenceEvent(
                event_id=101,
                document_id=501,
                event_type="news_rss_item",
                title="Nvidia H200 China deal survived the summit",
                summary="GPU export path stays open.",
                event_at="2026-05-19T10:02:40+00:00",
                source_name="rss_news:ai-semiconductor-cycle",
                external_document_id="rss:ai-semiconductor-cycle:abc",
                theme_key="AI_SEMICONDUCTOR_CYCLE",
                theme_name="AI Semiconductor Cycle",
                impact_direction="supportive",
                impact_score=0.66,
                symbol="NVDA",
            ),
            NewsRssClusterEvidenceEvent(
                event_id=103,
                document_id=503,
                event_type="news_rss_item",
                title="Treasury sell-off eases",
                summary="Rates remain in focus.",
                event_at="2026-05-19T09:10:00+00:00",
                source_name="rss_news:macro-rates-fed",
                external_document_id="rss:macro-rates-fed:abc",
                theme_key="MACRO_RATES_FED",
                theme_name="Macro Rates and Fed",
                impact_direction="risk_review",
                impact_score=0.68,
                symbol=None,
            ),
        )

        clusters = build_news_rss_clusters(events, as_of_date=date(2026, 5, 19), max_clusters=4)

        self.assertEqual(len(clusters), 2)
        self.assertEqual(clusters[0].theme_key, "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(clusters[0].symbols, ("NVDA",))
        artifact = json.loads(clusters[0].output_json())
        self.assertEqual(artifact["source"], "local_rules")
        self.assertEqual(artifact["cluster"]["event_count"], 1)

    def test_build_news_rss_clusters_keeps_one_cluster_per_event(self) -> None:
        events = (
            NewsRssClusterEvidenceEvent(
                event_id=101,
                document_id=501,
                event_type="news_rss_item",
                title="Treasury yields spike",
                summary="Rates remain in focus.",
                event_at="2026-05-19T10:02:40+00:00",
                source_name="rss_news:macro-rates-fed",
                external_document_id="rss:macro-rates-fed:abc",
                theme_key="MACRO_RATES_FED",
                theme_name="Macro Rates and Fed",
                impact_direction="watch",
                impact_score=0.80,
                symbol="SPY",
            ),
            NewsRssClusterEvidenceEvent(
                event_id=101,
                document_id=501,
                event_type="news_rss_item",
                title="Treasury yields spike",
                summary="Rates remain in focus.",
                event_at="2026-05-19T10:02:40+00:00",
                source_name="rss_news:macro-rates-fed",
                external_document_id="rss:macro-rates-fed:abc",
                theme_key="MARKET_NEWS_FLOW",
                theme_name="Market News Flow",
                impact_direction="watch",
                impact_score=0.55,
                symbol="SPY",
            ),
        )

        clusters = build_news_rss_clusters(events, as_of_date=date(2026, 5, 19), max_clusters=4)

        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0].theme_key, "MACRO_RATES_FED")
        self.assertEqual(clusters[0].events[0].event_id, 101)

    def test_run_news_rss_cluster_evidence_dry_run_does_not_write(self) -> None:
        executor = FakeExecutor()
        summary = run_news_rss_cluster_evidence(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            event_limit=10,
            max_clusters=2,
            dry_run=True,
            executor=executor,
        )

        self.assertEqual(summary["status"], "planned")
        self.assertEqual(summary["cluster_count"], 2)
        self.assertEqual(summary["planned_cluster_count"], 2)
        self.assertFalse(any("insert into ai.extraction_artifact" in sql for sql in executor.scalar_sql))
        self.assertEqual(executor.non_query_sql, [])

    def test_run_news_rss_cluster_evidence_writes_artifacts(self) -> None:
        executor = FakeExecutor()
        summary = run_news_rss_cluster_evidence(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            event_limit=10,
            max_clusters=2,
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 7001)
        self.assertEqual(summary["pipeline_name"], "news_rss_cluster_evidence")
        self.assertEqual(summary["inserted_artifact_count"], 2)
        self.assertEqual(summary["failed_cluster_count"], 0)
        self.assertTrue(any("insert into ai.model_invocation" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("insert into ai.extraction_artifact" in sql for sql in executor.scalar_sql))
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_news_rss_cluster_evidence_can_record_data_health_pipeline_name(self) -> None:
        executor = FakeExecutor()
        summary = run_news_rss_cluster_evidence(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            event_limit=10,
            max_clusters=1,
            pipeline_name="event_intelligence_llm_extract",
            executor=executor,
        )

        self.assertEqual(summary["pipeline_name"], "event_intelligence_llm_extract")
        self.assertTrue(
            any(
                "insert into ops.pipeline_run" in sql and "event_intelligence_llm_extract" in sql
                for sql in executor.scalar_sql
            )
        )

    def test_run_news_rss_cluster_evidence_rejects_empty_pipeline_name(self) -> None:
        with self.assertRaises(ValueError):
            run_news_rss_cluster_evidence(
                config=type("Config", (), {})(),
                pipeline_name=" ",
                executor=FakeExecutor(),
            )

    def test_run_news_rss_cluster_evidence_skips_existing_hash(self) -> None:
        executor = FakeExecutor(existing_artifact_id=9901)
        summary = run_news_rss_cluster_evidence(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            event_limit=10,
            max_clusters=1,
            executor=executor,
        )

        self.assertEqual(summary["inserted_artifact_count"], 0)
        self.assertEqual(summary["skipped_existing_count"], 1)
        self.assertFalse(any("insert into ai.extraction_artifact" in sql for sql in executor.scalar_sql))


if __name__ == "__main__":
    unittest.main()
