"""Real SQL checks, opt-in and restricted to the disposable local news database."""
import json
import os
from dataclasses import replace
from pathlib import Path
import unittest

from stockanalysis.ingest.news.rss import parse_news_rss_feed
from stockanalysis.ingest.news.sql import render_news_rss_upsert_sql
from stockanalysis.ingest.psql import PsqlCommandExecutor, PsqlExecutionError
from stockanalysis.operations.news_source_consistency import preview_news_source_quarantine, quarantine_news_source


@unittest.skipUnless(os.getenv("STOCKA_NEWS_TEST_ENABLED") == "1", "Disposable local PostgreSQL required")
class NewsSourceConsistencyPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executor = PsqlCommandExecutor(["/opt/homebrew/opt/postgresql@17/bin/psql", "-h", "/private/tmp", "-p", "55488", "-U", "postgres", "-d", "stocka_news_consistency_test"])
        if cls.executor.execute_scalar("select current_database();") != "stocka_news_consistency_test":
            raise RuntimeError("Refusing a non-test database")

    def setUp(self):
        self.executor.execute_non_query("drop schema if exists ops,ref,ingest,market,macro,event,signal,portfolio,performance,ai cascade;")
        root = Path(__file__).parents[1] / "db/migrations"
        for name in ("0001_bootstrap.sql", "0002_priority_1_tables.sql", "0003_priority_1_indexes.sql", "0005_ai_intelligence.sql", "0016_news_document_translation.sql"):
            self.executor.execute_non_query((root / name).read_text())
        self.executor.execute_non_query("""
insert into ref.market values('US','US','US','USD','UTC',true);
insert into ref.exchange(market_code,mic_code,name,timezone) values('US','TEST','Test','UTC');
insert into ref.issuer(legal_name,display_name,country_code,issuer_type) values('Apple','Apple','US','company');
insert into ref.instrument(issuer_id,exchange_id,market_code,primary_symbol,instrument_type,currency_code,name) values(1,1,'US','AAPL','equity','USD','Apple');
insert into ref.classification_node(taxonomy_family,node_type,code,name) values('theme','theme','AI','AI');
""")
        self.first = self.feed("Apple product", "https://example.test/apple")
        self.upsert(self.first)
        self.executor.execute_non_query("""
update ingest.source_document set korean_title='Old title', korean_summary='Old summary';
insert into event.event_instrument_impact(event_id,instrument_id,impact_direction,confidence) values(1,1,'supportive',.7);
insert into event.event_classification_impact(event_id,node_id,impact_direction,confidence) values(1,1,'supportive',.7);
insert into ai.document_chunk(document_id,chunk_index,content_hash,text_preview) values(1,0,'old','Original chunk');
insert into ai.model_invocation(task_name,provider,model_name,status) values('test','fixture','fixture','succeeded');
insert into ai.extraction_artifact(invocation_id,document_id,event_id,artifact_type,output_json) values(1,1,1,'test','{"saved":"unchanged"}');
""")

    def feed(self, title, url):
        return parse_news_rss_feed(f'<rss><channel><item><title>{title}</title><guid>?src=A00220&amp;yptr=yahoo</guid><link>{url}</link><pubDate>Thu, 10 Sep 2026 12:00:00 GMT</pubDate></item></channel></rss>', feed_name="test", feed_url="https://example.test/rss")

    def upsert(self, result):
        return json.loads(self.executor.execute_scalar(render_news_rss_upsert_sql(result)))

    def preview(self):
        return preview_news_source_quarantine(self.executor, document_id=1)

    def repair(self, preview):
        return quarantine_news_source(self.executor, document_id=1, expected_fingerprint=preview["fingerprint"], expected_external_id=self.first.items[0].external_document_id, expected_source_name="rss_news:test")

    def preserved_artifacts(self):
        return self.executor.execute_scalar("select jsonb_build_object('chunks',(select jsonb_agg(to_jsonb(c)) from ai.document_chunk c),'artifacts',(select jsonb_agg(to_jsonb(a)) from ai.extraction_artifact a))::text;")

    def test_distinct_articles_do_not_overwrite_translation_or_impacts_and_repeat_is_idempotent(self):
        before = self.preview()["snapshot"]
        second = self.feed("Drone earnings", "https://example.test/drone")
        self.upsert(second); self.upsert(second)
        self.assertEqual(before, self.preview()["snapshot"])
        self.assertEqual(self.executor.execute_scalar("select count(*) from ingest.source_document;"), "2")
        self.assertEqual(self.executor.execute_scalar("select count(*) from event.event;"), "2")

    def test_quarantine_archives_edges_preserves_history_and_replay_cannot_overwrite(self):
        before = self.preview(); artifacts = self.preserved_artifacts()
        receipt = self.repair(before)
        self.assertEqual(receipt["removed_instrument_impacts"], 1)
        self.assertEqual(receipt["removed_classification_impacts"], 1)
        archived = json.loads(self.executor.execute_scalar("select (config_json->'snapshot')::text from ops.pipeline_run;"))
        self.assertEqual(archived, before["snapshot"])
        after = self.preview()["snapshot"]
        self.assertEqual(after["instrument_impacts"], [])
        self.assertEqual(after["classification_impacts"], [])
        self.assertEqual(after["document"]["korean_title"], "Old title")
        self.assertEqual(artifacts, self.preserved_artifacts())
        self.assertEqual(after["links"], before["snapshot"]["links"])
        self.assertEqual(self.repair(before)["status"], "already_quarantined")
        overwritten = replace(self.first, items=(replace(self.first.items[0], title="Must not overwrite"),))
        self.assertEqual(self.upsert(overwritten)["source_document_count"], 0)
        self.assertEqual(after, self.preview()["snapshot"])
        self.assertEqual(self.executor.execute_scalar("select count(*) from ops.pipeline_run;"), "1")

    def test_stale_preview_fails_atomically(self):
        before = self.preview()
        self.executor.execute_non_query("update event.event_instrument_impact set confidence=.8;")
        with self.assertRaisesRegex(PsqlExecutionError, "changed after preview"):
            self.repair(before)
        self.assertEqual(self.executor.execute_scalar("select count(*) from ops.pipeline_run;"), "0")
        self.assertEqual(self.preview()["snapshot"]["document"]["document_type"], "news_rss_item")

    def test_multi_source_event_is_not_destructively_quarantined(self):
        self.upsert(self.feed("Separate article", "https://example.test/other"))
        self.executor.execute_non_query("insert into event.event_document_link values(1,2,'source');")
        with self.assertRaisesRegex(PsqlExecutionError, "isolated RSS"):
            self.repair(self.preview())
        self.assertEqual(len(self.preview()["snapshot"]["instrument_impacts"]), 1)
        self.assertEqual(self.executor.execute_scalar("select count(*) from ops.pipeline_run;"), "0")


if __name__ == "__main__": unittest.main()
