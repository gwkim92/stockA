from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.ingest.news.raw_body_chunk_index import (
    NewsRssRawBodyChunkCandidate,
    build_raw_body_chunks,
    extract_text_from_html,
    render_news_rss_raw_body_chunk_candidate_lookup_sql,
    render_news_rss_raw_body_chunk_upsert_sql,
    run_news_rss_raw_body_chunk_index,
)


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 991,
        candidate_rows: list[dict[str, object]] | None = None,
        fail_on_upsert: bool = False,
    ) -> None:
        self.run_id = run_id
        self.candidate_rows = candidate_rows if candidate_rows is not None else []
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "from ingest.source_document" in sql:
            return json.dumps(self.candidate_rows)
        if "insert into ai.document_chunk" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("chunk upsert failed")
            return json.dumps(
                {
                    "document_id": 61,
                    "external_document_id": "rss:fixture:article-1",
                    "chunk_count": 2,
                    "embedding_count": 2,
                    "stale_chunk_deleted_count": 0,
                    "stale_local_embedding_deleted_count": 1,
                }
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


def _candidate(*, raw_storage_uri: str) -> dict[str, object]:
    return {
        "document_id": 61,
        "external_document_id": "rss:fixture:article-1",
        "title": "AI demand accelerates",
        "summary": "Datacenter AI infrastructure demand is connected to power supply.",
        "url": "https://example.com/markets/ai-demand",
        "raw_storage_uri": raw_storage_uri,
        "checksum": "raw-checksum",
    }


def _candidate_model(*, raw_storage_uri: str) -> NewsRssRawBodyChunkCandidate:
    return NewsRssRawBodyChunkCandidate(
        document_id=61,
        external_document_id="rss:fixture:article-1",
        title="AI demand accelerates",
        raw_storage_uri=raw_storage_uri,
        checksum="raw-checksum",
        summary="Datacenter AI infrastructure demand is connected to power supply.",
        url="https://example.com/markets/ai-demand",
    )


class NewsRssRawBodyChunkIndexTests(unittest.TestCase):
    def test_render_candidate_lookup_sql_selects_raw_rss_documents(self) -> None:
        sql = render_news_rss_raw_body_chunk_candidate_lookup_sql(
            document_limit=8,
            external_document_id="rss:fixture:quote's",
            exclude_url_hosts=("https://news.google.com/rss/articles",),
        )

        self.assertIn("d.document_type = 'news_rss_item'", sql)
        self.assertIn("d.raw_storage_uri is not null", sql)
        self.assertIn("'summary', summary", sql)
        self.assertIn("'url', url", sql)
        self.assertIn("ds.source_kind = 'news_rss'", sql)
        self.assertIn("d.external_document_id = 'rss:fixture:quote''s'", sql)
        self.assertIn("not (d.url ~* '^https?://news\\.google\\.com([:/?#]|$)')", sql)
        self.assertIn("limit 8", sql)

    def test_extract_text_from_html_omits_script_style_and_normalizes_space(self) -> None:
        text = extract_text_from_html(
            """
            <html><head><style>.x{display:none}</style><script>alert(1)</script></head>
            <body><svg><path></path></svg><h1>Market cycle</h1><p>AI infrastructure   demand rises.</p></body></html>
            """
        )

        self.assertEqual(text, "Market cycle AI infrastructure demand rises.")
        self.assertNotIn("alert", text)
        self.assertNotIn("display", text)

    def test_extract_text_from_html_prefers_article_body_and_removes_common_boilerplate(self) -> None:
        text = extract_text_from_html(
            """
            <html>
              <body>
                <nav>Home Markets Subscribe</nav>
                <main>
                  <article>
                    <p>Skip to content</p>
                    <h1>Vera platform reaches AI labs</h1>
                    <p>NVIDIA shipped Vera systems to AI labs for agentic inference workloads.</p>
                    <p>Share This Article X Facebook LinkedIn Email Copy link Link copied! 0 Comments</p>
                  </article>
                </main>
                <footer>Privacy Terms Careers</footer>
              </body>
            </html>
            """
        )

        self.assertEqual(
            text,
            "Vera platform reaches AI labs NVIDIA shipped Vera systems to AI labs for agentic inference workloads.",
        )
        self.assertNotIn("Home Markets", text)
        self.assertNotIn("Skip to content", text)
        self.assertNotIn("Share This Article", text)
        self.assertNotIn("X Facebook", text)
        self.assertNotIn("Copy link", text)

    def test_build_raw_body_chunks_adds_local_no_cost_metadata(self) -> None:
        chunks = build_raw_body_chunks(
            candidate=_candidate_model(raw_storage_uri="file:///tmp/article.html"),
            text=" ".join(f"word{i}" for i in range(80)),
            max_text_chars=80,
            max_chunks_per_document=2,
        )

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].chunk_index, 0)
        self.assertEqual(len(chunks[0].content_hash), 64)
        self.assertEqual(chunks[0].metadata["chunker"], "rss-raw-html-text-v1")
        self.assertEqual(chunks[0].metadata["source_text_kind"], "raw_html_text")
        self.assertFalse(chunks[0].metadata["used_metadata_fallback"])
        self.assertFalse(chunks[0].metadata["external_embedding_api"])
        self.assertFalse(chunks[0].metadata["live_llm_call"])
        self.assertNotIn("raw_storage_uri", chunks[0].metadata)

    def test_render_upsert_sql_writes_chunks_and_replaces_local_stale_embeddings(self) -> None:
        chunks = build_raw_body_chunks(
            candidate=_candidate_model(raw_storage_uri="file:///tmp/article.html"),
            text="AI infrastructure demand rises as chips and power constraints matter.",
            max_text_chars=160,
            max_chunks_per_document=3,
        )
        sql = render_news_rss_raw_body_chunk_upsert_sql(
            candidate=_candidate_model(raw_storage_uri="file:///tmp/article.html"),
            chunks=chunks,
            provider="local_deterministic",
            model_name="rss_raw_html_text_hash_v1",
            embedding_dimension=1,
        )

        self.assertIn("insert into ai.document_chunk", sql)
        self.assertIn("delete from ai.document_chunk", sql)
        self.assertIn("delete from ai.embedding_index", sql)
        self.assertIn("insert into ai.embedding_index", sql)
        self.assertIn("'local://stockanalysis/news-rss/raw-body/document/'", sql)
        self.assertIn("'rss_raw_html_text_hash_v1'", sql)
        self.assertIn('"rss-raw-html-text-v1"', sql)
        self.assertIn('"external_embedding_api": false', sql)
        self.assertIn('"live_llm_call": false', sql)

    def test_build_raw_body_chunks_can_mark_metadata_fallback(self) -> None:
        chunks = build_raw_body_chunks(
            candidate=_candidate_model(raw_storage_uri="file:///tmp/article.html"),
            text="AI demand accelerates. Datacenter power matters.",
            max_text_chars=160,
            max_chunks_per_document=1,
            source_text_kind="source_document_metadata_fallback",
            used_metadata_fallback=True,
        )

        self.assertEqual(chunks[0].metadata["source_text_kind"], "source_document_metadata_fallback")
        self.assertTrue(chunks[0].metadata["used_metadata_fallback"])

    def test_run_raw_body_chunk_index_reads_artifact_and_updates_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "article.html"
            artifact_path.write_text(
                "<html><body><h1>AI chips</h1><p>Datacenter demand and power supply are linked.</p></body></html>",
                encoding="utf-8",
            )
            executor = FakeExecutor(candidate_rows=[_candidate(raw_storage_uri=artifact_path.as_uri())])

            summary = run_news_rss_raw_body_chunk_index(
                config=type("Config", (), {})(),
                document_limit=1,
                artifact_root=tmpdir,
                max_text_chars=40,
                max_chunks_per_document=2,
                executor=executor,
            )

        self.assertEqual(summary["run_id"], 991)
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["succeeded_document_count"], 1)
        self.assertEqual(summary["failed_document_count"], 0)
        self.assertEqual(summary["chunk_count"], 2)
        self.assertEqual(summary["embedding_count"], 2)
        self.assertEqual(summary["results"][0]["status"], "succeeded")
        self.assertIn("AI chips", str(summary["results"][0]["text_preview"]))
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("'ai'", executor.scalar_sql[0])
        self.assertIn("news_rss_raw_body_chunk_index", executor.scalar_sql[0])
        self.assertIn("insert into ai.document_chunk", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])
        self.assertEqual(summary["exclude_url_hosts"], [])

    def test_run_raw_body_chunk_index_records_excluded_hosts(self) -> None:
        executor = FakeExecutor(candidate_rows=[])

        summary = run_news_rss_raw_body_chunk_index(
            config=type("Config", (), {})(),
            exclude_url_hosts=("https://news.google.com/rss/articles",),
            executor=executor,
        )

        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["requested_document_count"], 0)
        self.assertEqual(summary["exclude_url_hosts"], ["news.google.com"])
        self.assertIn("news.google.com", executor.scalar_sql[0])
        self.assertIn("not (d.url ~* '^https?://news\\.google\\.com([:/?#]|$)')", executor.scalar_sql[1])

    def test_run_raw_body_chunk_index_skips_duplicate_raw_checksums_within_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first_path = Path(tmpdir) / "first.html"
            first_path.write_text("<html><body><article>First clean article body about AI chips.</article></body></html>", encoding="utf-8")
            duplicate_path = Path(tmpdir) / "duplicate.html"
            duplicate_path.write_text(
                "<html><body><article>Duplicate mirrored article body about AI chips.</article></body></html>",
                encoding="utf-8",
            )
            executor = FakeExecutor(
                candidate_rows=[
                    _candidate(raw_storage_uri=first_path.as_uri()),
                    _candidate(
                        raw_storage_uri=duplicate_path.as_uri()
                    )
                    | {
                        "document_id": 62,
                        "external_document_id": "rss:fixture:article-duplicate",
                    },
                ]
            )

            summary = run_news_rss_raw_body_chunk_index(
                config=type("Config", (), {})(),
                artifact_root=tmpdir,
                executor=executor,
            )

        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["requested_document_count"], 2)
        self.assertEqual(summary["succeeded_document_count"], 1)
        self.assertEqual(summary["skipped_duplicate_document_count"], 1)
        self.assertEqual(summary["results"][1]["status"], "skipped_duplicate_raw_checksum")
        self.assertEqual(sum(1 for sql in executor.scalar_sql if "insert into ai.document_chunk" in sql), 1)

    def test_run_raw_body_chunk_index_rejects_artifact_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as outside_dir:
            outside_path = Path(outside_dir) / "article.html"
            outside_path.write_text("<html><body>outside</body></html>", encoding="utf-8")
            executor = FakeExecutor(candidate_rows=[_candidate(raw_storage_uri=outside_path.as_uri())])

            summary = run_news_rss_raw_body_chunk_index(
                config=type("Config", (), {})(),
                artifact_root=root_dir,
                executor=executor,
            )

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["failed_document_count"], 1)
        self.assertIn("under artifact_root", str(summary["results"][0]["error"]))
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])

    def test_run_raw_body_chunk_index_falls_back_to_metadata_when_html_has_no_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "article.html"
            artifact_path.write_text("<html><script>" + ("var x = 1;" * 100), encoding="utf-8")
            executor = FakeExecutor(candidate_rows=[_candidate(raw_storage_uri=artifact_path.as_uri())])

            summary = run_news_rss_raw_body_chunk_index(
                config=type("Config", (), {})(),
                artifact_root=tmpdir,
                executor=executor,
            )

        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["succeeded_document_count"], 1)
        self.assertTrue(summary["results"][0]["used_metadata_fallback"])
        self.assertEqual(summary["results"][0]["source_text_kind"], "source_document_metadata_fallback")
        self.assertIn("AI demand accelerates", str(summary["results"][0]["text_preview"]))

    def test_run_raw_body_chunk_index_marks_failed_when_upsert_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "article.html"
            artifact_path.write_text("<html><body>AI article body</body></html>", encoding="utf-8")
            executor = FakeExecutor(candidate_rows=[_candidate(raw_storage_uri=artifact_path.as_uri())], fail_on_upsert=True)

            summary = run_news_rss_raw_body_chunk_index(
                config=type("Config", (), {})(),
                artifact_root=tmpdir,
                executor=executor,
            )

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["failed_document_count"], 1)
        self.assertIn("chunk upsert failed", str(summary["results"][0]["error"]))
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])


if __name__ == "__main__":
    unittest.main()
