from __future__ import annotations

import json
import unittest
from pathlib import Path

from stockanalysis.ingest.news.rss import load_news_rss_sync_result, parse_news_rss_feed
from stockanalysis.ingest.news.sql import render_news_rss_upsert_sql
from stockanalysis.ingest.news.upsert import run_news_rss_upsert


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(self, *, run_id: int = 301, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if self.fail_on_upsert:
            raise RuntimeError("boom")
        return json.dumps(
            {
                "requested_item_count": 2,
                "source_document_count": 2,
                "event_count": 2,
                "linked_document_count": 2,
            }
        )

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class NewsRssTests(unittest.TestCase):
    def test_load_news_rss_sync_result_from_fixture(self) -> None:
        result = load_news_rss_sync_result(
            feed_name="fixture",
            feed_url="https://example.com/rss",
            config=type("Config", (), {})(),
            feed_xml_path=str(FIXTURES_DIR / "news_rss_sample.xml"),
        )

        self.assertEqual(result.feed_name, "fixture")
        self.assertEqual(len(result.items), 2)
        first = result.items[0]
        self.assertEqual(first.title, "Apple supplier orders point to AI device cycle")
        self.assertEqual(first.summary, "Apple suppliers reported stronger component orders tied to AI-enabled devices.")
        self.assertEqual(first.language, "en-US")
        self.assertEqual(first.published_at.isoformat(), "2026-05-19T10:00:00+00:00")
        self.assertTrue(first.external_document_id.startswith("rss:fixture:"))

    def test_news_rss_external_document_id_is_deterministic(self) -> None:
        first = load_news_rss_sync_result(
            feed_name="fixture",
            feed_url="https://example.com/rss",
            config=type("Config", (), {})(),
            feed_xml_path=str(FIXTURES_DIR / "news_rss_sample.xml"),
            limit=1,
        )
        second = load_news_rss_sync_result(
            feed_name="fixture",
            feed_url="https://example.com/rss",
            config=type("Config", (), {})(),
            feed_xml_path=str(FIXTURES_DIR / "news_rss_sample.xml"),
            limit=1,
        )

        self.assertEqual(first.items[0].external_document_id, second.items[0].external_document_id)
        self.assertEqual(first.items[0].checksum, second.items[0].checksum)

    def test_parse_atom_feed(self) -> None:
        result = parse_news_rss_feed(
            """<?xml version="1.0" encoding="UTF-8"?>
            <feed xmlns="http://www.w3.org/2005/Atom">
              <entry>
                <title>Semiconductor capex cycle improves</title>
                <id>tag:example.com,2026:semi-cycle</id>
                <link href="https://example.com/semi-cycle" />
                <updated>2026-05-19T12:00:00Z</updated>
                <summary>Memory demand stabilized.</summary>
              </entry>
            </feed>""",
            feed_name="atom-fixture",
            feed_url="https://example.com/atom",
        )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].url, "https://example.com/semi-cycle")
        self.assertEqual(result.items[0].published_at.isoformat(), "2026-05-19T12:00:00+00:00")

    def test_render_news_rss_upsert_sql_writes_source_documents_events_and_links(self) -> None:
        result = load_news_rss_sync_result(
            feed_name="fixture",
            feed_url="https://example.com/rss",
            config=type("Config", (), {})(),
            feed_xml_path=str(FIXTURES_DIR / "news_rss_sample.xml"),
            limit=1,
        )
        sql = render_news_rss_upsert_sql(result, ingested_by_run_id=501)

        self.assertIn("insert into ingest.data_source", sql)
        self.assertIn("rss_news:fixture", sql)
        self.assertIn("insert into ingest.source_document", sql)
        self.assertIn("'news_rss_item'", sql)
        self.assertIn("insert into event.event", sql)
        self.assertIn("insert into event.event_document_link", sql)
        self.assertIn("501::bigint", sql)
        self.assertIn("on conflict (data_source_id, external_document_id)", sql)
        self.assertIn("on conflict (dedupe_key)", sql)

    def test_run_news_rss_upsert_records_pipeline_run(self) -> None:
        executor = FakeExecutor(run_id=77)
        summary = run_news_rss_upsert(
            feed_name="fixture",
            feed_url="https://example.com/rss",
            config=type("Config", (), {})(),
            feed_xml_path=str(FIXTURES_DIR / "news_rss_sample.xml"),
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["requested_item_count"], 2)
        self.assertEqual(summary["source_document_count"], 2)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("77::bigint", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_news_rss_upsert_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=78, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_news_rss_upsert(
                feed_name="fixture",
                feed_url="https://example.com/rss",
                config=type("Config", (), {})(),
                feed_xml_path=str(FIXTURES_DIR / "news_rss_sample.xml"),
                executor=executor,
            )

        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])


if __name__ == "__main__":
    unittest.main()
