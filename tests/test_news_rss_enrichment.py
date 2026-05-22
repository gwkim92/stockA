from __future__ import annotations

import json
import unittest

from stockanalysis.ingest.news.enrichment import (
    classify_theme,
    detect_instrument_symbol,
    infer_impact_direction_and_strength,
    load_pending_news_rss_event_enrichment_candidates,
    resolve_instrument_for_candidate,
    run_news_rss_event_enrichment,
)
from stockanalysis.ingest.news.models import NewsRssEventEnrichmentCandidate
from stockanalysis.ingest.news.sql import (
    render_instrument_lookup_by_company_alias_sql,
    render_news_rss_classification_bootstrap_sql,
    render_pending_news_rss_event_enrichment_candidates_sql,
)
from stockanalysis.ingest.psql import PsqlExecutionError


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 1201,
        missing_instrument: bool = False,
        fail_on_classification: bool = False,
        pending_candidates: list[dict[str, object]] | None = None,
    ) -> None:
        self.run_id = run_id
        self.missing_instrument = missing_instrument
        self.fail_on_classification = fail_on_classification
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.pending_candidates = pending_candidates or [
            {
                "event_id": 31,
                "event_type": "news_rss_item",
                "dedupe_key": "news_rss:rss:ai-semiconductor-cycle:abc",
                "title": "Nvidia H200 China deal survived the summit",
                "summary": "GPU export path stays open.",
                "source_name": "rss_news:ai-semiconductor-cycle",
                "external_document_id": "rss:ai-semiconductor-cycle:abc",
            },
            {
                "event_id": 32,
                "event_type": "news_rss_item",
                "dedupe_key": "news_rss:rss:macro-rates-fed:def",
                "title": "Treasury sell-off eases as Fed credibility is tested",
                "summary": "Sticky prices keep rates in focus.",
                "source_name": "rss_news:macro-rates-fed",
                "external_document_id": "rss:macro-rates-fed:def",
            },
        ]
        self.instrument_payload = {
            "instrument_id": 701,
            "primary_symbol": "NVDA",
            "instrument_name": "NVIDIA Corp",
        }
        self.alias_payloads = {
            "analog devices": {
                "instrument_id": 702,
                "primary_symbol": "ADI",
                "instrument_name": "ANALOG DEVICES INC",
            },
            "intuit": {
                "instrument_id": 703,
                "primary_symbol": "INTU",
                "instrument_name": "INTUIT INC.",
            },
        }

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from event.event e" in sql:
            return json.dumps(self.pending_candidates)
        if "instrument_aliases" in sql:
            lowered_sql = sql.lower()
            for alias, payload in self.alias_payloads.items():
                if alias in lowered_sql:
                    return json.dumps(payload)
            raise PsqlExecutionError("psql returned no rows for scalar query")
        if "from ref.instrument i" in sql:
            if self.missing_instrument:
                raise PsqlExecutionError("psql returned no rows for scalar query")
            return json.dumps(self.instrument_payload)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_classification and "insert into event.event_classification_impact" in sql:
            raise RuntimeError("boom")


class NewsRssEnrichmentTests(unittest.TestCase):
    def test_render_pending_news_rss_event_enrichment_candidates_sql(self) -> None:
        sql = render_pending_news_rss_event_enrichment_candidates_sql(limit=8)

        self.assertIn("event.event_classification_impact", sql)
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("e.dedupe_key like 'news_rss:%'", sql)
        self.assertIn("limit 8", sql)

    def test_render_news_rss_classification_bootstrap_sql(self) -> None:
        sql = render_news_rss_classification_bootstrap_sql()

        self.assertIn("MARKET_NEWS_FLOW", sql)
        self.assertIn("QUANTUM_COMPUTING_POLICY", sql)
        self.assertIn("AI_SEMICONDUCTOR_CYCLE", sql)
        self.assertIn("MACRO_RATES_FED", sql)
        self.assertIn("insert into ref.classification_edge", sql)

    def test_render_company_alias_lookup_matches_instrument_name_not_manual_symbol_list(self) -> None:
        sql = render_instrument_lookup_by_company_alias_sql(
            title="Dear Analog Devices Stock Fans, Mark Your Calendars",
            summary="",
        )

        self.assertIn("instrument_aliases", sql)
        self.assertIn("Analog Devices", sql)
        self.assertIn("regexp_replace(lower(", sql)
        self.assertIn("instrument_type = 'listed_security'", sql)
        self.assertIn("'financial institutions'", sql)
        self.assertIn("company_alias", sql)

    def test_load_pending_news_rss_event_enrichment_candidates(self) -> None:
        executor = FakeExecutor()
        candidates = load_pending_news_rss_event_enrichment_candidates(limit=10, executor=executor)

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].event_id, 31)
        self.assertEqual(candidates[0].source_name, "rss_news:ai-semiconductor-cycle")

    def test_rule_classification_detects_theme_instrument_and_risk(self) -> None:
        candidate = NewsRssEventEnrichmentCandidate(
            event_id=31,
            event_type="news_rss_item",
            dedupe_key="news_rss:x",
            title="Nvidia H200 China deal survived the summit",
            summary="GPU export path stays open.",
            source_name="rss_news:ai-semiconductor-cycle",
            external_document_id="rss:x",
        )

        self.assertEqual(classify_theme(candidate).node_code, "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(detect_instrument_symbol(candidate), "NVDA")
        self.assertEqual(infer_impact_direction_and_strength(candidate)[0], "supportive")

    def test_rule_classification_detects_quantum_policy_news(self) -> None:
        candidate = NewsRssEventEnrichmentCandidate(
            event_id=55,
            event_type="news_rss_item",
            dedupe_key="news_rss:rss:marketwatch-topstories:quantum",
            title="Quantum stocks soar as the Trump administration looks to be buying in",
            summary="The administration is considering funding and stakes in quantum computing companies.",
            source_name="rss_news:marketwatch-topstories",
            external_document_id="rss:marketwatch-topstories:quantum",
        )

        self.assertEqual(classify_theme(candidate).node_code, "QUANTUM_COMPUTING_POLICY")
        self.assertEqual(detect_instrument_symbol(candidate), "QUBT")
        self.assertEqual(infer_impact_direction_and_strength(candidate)[0], "supportive")

    def test_company_alias_resolution_links_obvious_named_company(self) -> None:
        candidate = NewsRssEventEnrichmentCandidate(
            event_id=33,
            event_type="news_rss_item",
            dedupe_key="news_rss:x",
            title="Dear Analog Devices Stock Fans, Mark Your Calendars for May 20",
            summary="",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:x",
        )

        symbol, instrument = resolve_instrument_for_candidate(candidate, executor=FakeExecutor())

        self.assertEqual(symbol, "ADI")
        self.assertIsNotNone(instrument)
        self.assertEqual(instrument.primary_symbol if instrument else None, "ADI")

    def test_company_alias_resolution_links_single_word_stock_phrase(self) -> None:
        candidate = NewsRssEventEnrichmentCandidate(
            event_id=34,
            event_type="news_rss_item",
            dedupe_key="news_rss:x",
            title="Dear Intuit Stock Fans, Mark Your Calendars for May 20",
            summary="",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:x",
        )

        symbol, instrument = resolve_instrument_for_candidate(candidate, executor=FakeExecutor())

        self.assertEqual(symbol, "INTU")
        self.assertIsNotNone(instrument)
        self.assertEqual(instrument.primary_symbol if instrument else None, "INTU")

    def test_run_news_rss_event_enrichment_dry_run_does_not_write(self) -> None:
        executor = FakeExecutor(run_id=1202)
        summary = run_news_rss_event_enrichment(
            config=type("Config", (), {})(),
            limit=10,
            dry_run=True,
            executor=executor,
        )

        self.assertEqual(summary["run_id"], None)
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["planned_event_count"], 2)
        self.assertEqual(executor.non_query_sql, [])
        self.assertFalse(any("insert into ops.pipeline_run" in sql for sql in executor.scalar_sql))

    def test_run_news_rss_event_enrichment_writes_theme_and_instrument_impacts(self) -> None:
        executor = FakeExecutor(run_id=1203)
        summary = run_news_rss_event_enrichment(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 1203)
        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 2)
        self.assertEqual(summary["failed_event_count"], 0)
        self.assertEqual(summary["instrument_linked_event_count"], 1)
        self.assertIn("insert into ref.classification_node", executor.non_query_sql[0])
        self.assertTrue(any("insert into event.event_classification_impact" in sql for sql in executor.non_query_sql))
        self.assertTrue(any("insert into event.event_instrument_impact" in sql for sql in executor.non_query_sql))
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_news_rss_event_enrichment_writes_company_alias_instrument_impacts(self) -> None:
        executor = FakeExecutor(
            run_id=1206,
            pending_candidates=[
                {
                    "event_id": 33,
                    "event_type": "news_rss_item",
                    "dedupe_key": "news_rss:rss:yahoo-finance-news:adi",
                    "title": "Dear Analog Devices Stock Fans, Mark Your Calendars for May 20",
                    "summary": "",
                    "source_name": "rss_news:yahoo-finance-news",
                    "external_document_id": "rss:yahoo-finance-news:adi",
                }
            ],
        )

        summary = run_news_rss_event_enrichment(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )

        self.assertEqual(summary["instrument_linked_event_count"], 1)
        self.assertEqual(summary["results"][0]["instrument_symbol"], "ADI")
        self.assertTrue(any("702" in sql for sql in executor.non_query_sql))

    def test_run_news_rss_event_enrichment_missing_instrument_is_not_failure(self) -> None:
        executor = FakeExecutor(run_id=1204, missing_instrument=True)
        summary = run_news_rss_event_enrichment(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )

        self.assertEqual(summary["failed_event_count"], 0)
        self.assertEqual(summary["instrument_linked_event_count"], 0)
        self.assertEqual(summary["instrument_skipped_event_count"], 2)
        self.assertIn("succeeded_instrument_missing", {result["status"] for result in summary["results"]})

    def test_run_news_rss_event_enrichment_continues_after_failure(self) -> None:
        executor = FakeExecutor(run_id=1205, fail_on_classification=True)
        summary = run_news_rss_event_enrichment(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )

        self.assertEqual(summary["requested_event_count"], 2)
        self.assertEqual(summary["succeeded_event_count"], 0)
        self.assertEqual(summary["failed_event_count"], 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


if __name__ == "__main__":
    unittest.main()
