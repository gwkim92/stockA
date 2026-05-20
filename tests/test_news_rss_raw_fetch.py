from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.ingest.models import FetchResponse, HttpRequest
from stockanalysis.ingest.news.raw_fetch import (
    render_news_rss_raw_fetch_candidate_lookup_sql,
    run_news_rss_raw_fetch,
)


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 901,
        candidate_rows: list[dict[str, object]] | None = None,
        fail_on_update: bool = False,
    ) -> None:
        self.run_id = run_id
        self.candidate_rows = candidate_rows if candidate_rows is not None else [_candidate_row()]
        self.fail_on_update = fail_on_update
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "from ingest.source_document" in sql:
            return json.dumps(self.candidate_rows)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_update and "update ingest.source_document" in sql:
            raise RuntimeError("update failed")


def _candidate_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "document_id": 51,
        "external_document_id": "rss:free-feed:article-1",
        "title": "AI infrastructure demand accelerates",
        "url": "https://example.com/markets/ai-infrastructure.html",
        "raw_storage_uri": None,
        "checksum": "feed-checksum",
    }
    row.update(overrides)
    return row


class CaptureFetcher:
    def __init__(self, response: FetchResponse) -> None:
        self.response = response
        self.requests: list[HttpRequest] = []

    def __call__(self, request: HttpRequest) -> FetchResponse:
        self.requests.append(request)
        return self.response


class NewsRssRawFetchTests(unittest.TestCase):
    def test_render_candidate_lookup_sql_discovers_pending_rss_documents(self) -> None:
        sql = render_news_rss_raw_fetch_candidate_lookup_sql(
            limit=7,
            external_document_id="rss:fixture:quote's",
            exclude_url_hosts=("https://news.google.com/rss/articles",),
        )

        self.assertIn("d.document_type = 'news_rss_item'", sql)
        self.assertIn("d.raw_storage_uri is null", sql)
        self.assertIn("d.url is not null", sql)
        self.assertIn("ds.source_kind = 'news_rss'", sql)
        self.assertIn("d.external_document_id = 'rss:fixture:quote''s'", sql)
        self.assertIn("not (d.url ~* '^https?://news\\.google\\.com([:/?#]|$)')", sql)
        self.assertIn("limit 7", sql)

    def test_render_candidate_lookup_sql_allows_force_refetch(self) -> None:
        sql = render_news_rss_raw_fetch_candidate_lookup_sql(limit=3, force=True)

        self.assertNotIn("d.raw_storage_uri is null", sql)
        self.assertIn("limit 3", sql)

    def test_run_news_rss_raw_fetch_writes_artifact_and_updates_document(self) -> None:
        executor = FakeExecutor(run_id=777)
        fetcher = CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"<html>article body</html>"))

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = run_news_rss_raw_fetch(
                config=type("Config", (), {})(),
                limit=1,
                artifact_root=tmpdir,
                user_agent="test-agent@example.com",
                executor=executor,
                fetcher=fetcher,
            )

            self.assertEqual(summary["run_id"], 777)
            self.assertEqual(summary["status"], "completed")
            self.assertEqual(summary["succeeded_document_count"], 1)
            self.assertEqual(summary["failed_document_count"], 0)
            result = summary["results"][0]
            self.assertEqual(result["status"], "succeeded")
            self.assertTrue(Path(str(result["artifact_path"])).exists())
            self.assertTrue(str(result["raw_storage_uri"]).startswith("file://"))
            self.assertEqual(len(str(result["checksum"])), 64)
            self.assertEqual(fetcher.requests[0].headers["User-Agent"], "test-agent@example.com")
            self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
            self.assertIn("news_rss_raw_fetch", executor.scalar_sql[0])
            self.assertIn("update ingest.source_document", executor.non_query_sql[0])
            self.assertIn("raw_storage_uri", executor.non_query_sql[0])
            self.assertIn("status = 'succeeded'", executor.non_query_sql[1])
            self.assertEqual(summary["exclude_url_hosts"], [])

    def test_run_news_rss_raw_fetch_records_excluded_hosts(self) -> None:
        executor = FakeExecutor(candidate_rows=[])

        summary = run_news_rss_raw_fetch(
            config=type("Config", (), {})(),
            exclude_url_hosts=("https://news.google.com/rss/articles",),
            executor=executor,
            fetcher=CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"unused")),
        )

        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["requested_document_count"], 0)
        self.assertEqual(summary["exclude_url_hosts"], ["news.google.com"])
        self.assertIn("news.google.com", executor.scalar_sql[0])
        self.assertIn("not (d.url ~* '^https?://news\\.google\\.com([:/?#]|$)')", executor.scalar_sql[1])

    def test_run_news_rss_raw_fetch_skips_existing_raw_without_force(self) -> None:
        executor = FakeExecutor(
            candidate_rows=[
                _candidate_row(
                    raw_storage_uri="file:///tmp/news/rss/article.html",
                    checksum="abc123",
                )
            ]
        )

        summary = run_news_rss_raw_fetch(
            config=type("Config", (), {})(),
            executor=executor,
            fetcher=CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"unused")),
        )

        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["skipped_document_count"], 1)
        self.assertEqual(summary["succeeded_document_count"], 0)
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_news_rss_raw_fetch_blocks_private_url_and_marks_failed(self) -> None:
        executor = FakeExecutor(candidate_rows=[_candidate_row(url="http://127.0.0.1/private")])

        summary = run_news_rss_raw_fetch(
            config=type("Config", (), {})(),
            executor=executor,
            fetcher=CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"unused")),
        )

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["failed_document_count"], 1)
        self.assertIn("private or local IP", str(summary["results"][0]["error"]))
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])

    def test_run_news_rss_raw_fetch_marks_failed_when_update_errors(self) -> None:
        executor = FakeExecutor(fail_on_update=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = run_news_rss_raw_fetch(
                config=type("Config", (), {})(),
                artifact_root=tmpdir,
                executor=executor,
                fetcher=CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"body")),
            )

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["failed_document_count"], 1)
        self.assertIn("update failed", str(summary["results"][0]["error"]))
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("update ingest.source_document", executor.non_query_sql[0])
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_body_file_requires_external_document_id(self) -> None:
        with self.assertRaises(ValueError):
            run_news_rss_raw_fetch(
                config=type("Config", (), {})(),
                body_path="article.html",
                executor=FakeExecutor(),
            )

    def test_run_news_rss_raw_fetch_truncates_large_body(self) -> None:
        executor = FakeExecutor()
        fetcher = CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"abcdef"))

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = run_news_rss_raw_fetch(
                config=type("Config", (), {})(),
                artifact_root=tmpdir,
                max_body_bytes=3,
                executor=executor,
                fetcher=fetcher,
            )

        result = summary["results"][0]
        self.assertEqual(result["byte_count"], 3)
        self.assertTrue(result["truncated"])

    def test_run_news_rss_raw_fetch_keeps_html_extension_for_long_extensionless_url_path(self) -> None:
        executor = FakeExecutor(
            candidate_rows=[
                _candidate_row(
                    url="https://news.google.com/rss/articles/" + ("a" * 240),
                )
            ]
        )
        fetcher = CaptureFetcher(FetchResponse(status_code=200, content_type="text/html", body=b"body"))

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = run_news_rss_raw_fetch(
                config=type("Config", (), {})(),
                artifact_root=tmpdir,
                executor=executor,
                fetcher=fetcher,
            )

        result = summary["results"][0]
        self.assertTrue(str(result["artifact_path"]).endswith(".html"))
        self.assertLessEqual(len(Path(str(result["artifact_path"])).name), 155)


if __name__ == "__main__":
    unittest.main()
