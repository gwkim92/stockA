from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.news_rss_feed_runner import (
    NEWS_RSS_FEED_CONFIG_VERSION,
    build_news_rss_config_report,
    load_news_rss_feed_config,
    run_news_rss_configured_feeds,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.next_run_id = 100
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            self.next_run_id += 1
            return str(self.next_run_id)
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


class NewsRssFeedRunnerTests(unittest.TestCase):
    def test_load_news_rss_feed_config_requires_repo_outside_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            config_path = Path(repo_root) / "feeds.json"
            config_path.write_text(json.dumps(_feed_config_payload()), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "outside repository"):
                load_news_rss_feed_config(config_path, repo_root=repo_root)

    def test_build_news_rss_config_report_redacts_full_urls(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            config_path = _write_feed_config(Path(outside_root))

            report = build_news_rss_config_report(config_path=config_path, repo_root=repo_root)
            report_text = json.dumps(report)

            self.assertEqual(report["report_name"], "news_rss_feed_config")
            self.assertEqual(report["enabled_feed_count"], 2)
            self.assertIn("example.com", report_text)
            self.assertNotIn("https://example.com/markets/rss", report_text)
            self.assertEqual(report["redaction_policy"], "full_feed_urls_omitted")

    def test_run_news_rss_configured_feeds_dry_run_does_not_execute_db(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            config_path = _write_feed_config(Path(outside_root))
            executor = FakeExecutor()

            report = run_news_rss_configured_feeds(
                config=RuntimeConfig(),
                feed_config_path=config_path,
                repo_root=repo_root,
                dry_run=True,
                executor=executor,
            )

            self.assertEqual(report["status"], "dry_run")
            self.assertEqual(report["enabled_feed_count"], 2)
            self.assertEqual(executor.scalar_sql, [])

    def test_run_news_rss_configured_feeds_executes_enabled_feeds(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            fixture_xml = outside_path / "feed.xml"
            fixture_xml.write_text(_sample_rss_xml(), encoding="utf-8")
            config_path = _write_feed_config(outside_path, fixture_xml=fixture_xml)
            executor = FakeExecutor()

            report = run_news_rss_configured_feeds(
                config=RuntimeConfig(),
                feed_config_path=config_path,
                repo_root=repo_root,
                executor=executor,
            )

            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["succeeded_feed_count"], 2)
            self.assertEqual(report["failed_feed_count"], 0)
            self.assertEqual(report["requested_item_count"], 4)
            self.assertEqual(report["source_document_count"], 4)
            self.assertEqual(len(executor.non_query_sql), 2)
            self.assertNotIn("https://example.com/markets/rss", json.dumps(report))

    def test_run_news_rss_configured_feeds_can_select_single_feed(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            fixture_xml = outside_path / "feed.xml"
            fixture_xml.write_text(_sample_rss_xml(), encoding="utf-8")
            config_path = _write_feed_config(outside_path, fixture_xml=fixture_xml)
            executor = FakeExecutor()

            report = run_news_rss_configured_feeds(
                config=RuntimeConfig(),
                feed_config_path=config_path,
                repo_root=repo_root,
                feed_names=("macro-feed",),
                executor=executor,
            )

            self.assertEqual(report["feed_count"], 1)
            self.assertEqual(report["enabled_feed_count"], 1)
            self.assertEqual(report["succeeded_feed_count"], 1)
            self.assertEqual(report["feeds"][0]["feed_name"], "macro-feed")


def _write_feed_config(outside_root: Path, *, fixture_xml: Path | None = None) -> Path:
    config_path = outside_root / "news-rss-feeds.json"
    config_path.write_text(json.dumps(_feed_config_payload(fixture_xml=fixture_xml)), encoding="utf-8")
    return config_path


def _feed_config_payload(*, fixture_xml: Path | None = None) -> dict[str, object]:
    feed_xml = str(fixture_xml) if fixture_xml is not None else None
    first_feed: dict[str, object] = {
        "feed_name": "market-feed",
        "feed_url": "https://example.com/markets/rss",
        "enabled": True,
        "limit": 2,
        "default_language": "en",
    }
    second_feed: dict[str, object] = {
        "feed_name": "macro-feed",
        "feed_url": "https://news.example.org/macro.xml",
        "enabled": True,
        "limit": 2,
        "default_language": "en",
    }
    if feed_xml is not None:
        first_feed["feed_xml_path"] = feed_xml
        second_feed["feed_xml_path"] = feed_xml
    return {
        "version": NEWS_RSS_FEED_CONFIG_VERSION,
        "feeds": [first_feed, second_feed],
    }


def _sample_rss_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Free Feed</title>
    <item>
      <title>First free feed item</title>
      <link>https://publisher.example/free/one</link>
      <guid>free-one</guid>
      <pubDate>Tue, 19 May 2026 10:00:00 GMT</pubDate>
      <description>First item.</description>
    </item>
    <item>
      <title>Second free feed item</title>
      <link>https://publisher.example/free/two</link>
      <guid>free-two</guid>
      <pubDate>Tue, 19 May 2026 11:00:00 GMT</pubDate>
      <description>Second item.</description>
    </item>
  </channel>
</rss>
"""


if __name__ == "__main__":
    unittest.main()
