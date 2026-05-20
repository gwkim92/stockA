from __future__ import annotations

import json
import unittest

from stockanalysis.ingest.news.chunk_index import (
    DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME,
    DEFAULT_RSS_CHUNK_INDEX_PROVIDER,
    render_news_rss_local_chunk_index_sql,
    run_news_rss_local_chunk_index,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 901, fail_on_index: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_index = fail_on_index
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if self.fail_on_index:
            raise RuntimeError("boom")
        return json.dumps(
            {
                "report_name": "news_rss_local_chunk_index",
                "provider": DEFAULT_RSS_CHUNK_INDEX_PROVIDER,
                "model_name": DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME,
                "embedding_dimension": 1,
                "document_limit": 25,
                "candidate_document_count": 2,
                "chunk_count": 2,
                "embedding_count": 2,
                "stale_embedding_deleted_count": 0,
                "external_embedding_api": False,
                "live_llm_call": False,
            }
        )

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class NewsRssChunkIndexTests(unittest.TestCase):
    def test_render_news_rss_local_chunk_index_sql_writes_chunks_and_embedding_metadata(self) -> None:
        sql = render_news_rss_local_chunk_index_sql(document_limit=25, max_text_chars=1200)

        self.assertIn("-- news rss local chunk index upsert", sql)
        self.assertIn("d.document_type = 'news_rss_item'", sql)
        self.assertIn("insert into ai.document_chunk", sql)
        self.assertIn("insert into ai.embedding_index", sql)
        self.assertIn("delete from ai.embedding_index", sql)
        self.assertIn("'[[:space:]]+'", sql)
        self.assertIn("on conflict (document_id, chunk_index)", sql)
        self.assertIn("on conflict (chunk_id, provider, model_name, content_hash)", sql)
        self.assertIn("'stale_embedding_deleted_count'", sql)
        self.assertIn("'local_deterministic'", sql)
        self.assertIn("'rss_title_summary_hash_v1'", sql)
        self.assertIn("'local://stockanalysis/news-rss/document/'", sql)
        self.assertIn("'external_embedding_api', false", sql)
        self.assertIn("'live_llm_call', false", sql)
        self.assertNotIn("openai", sql.lower())
        self.assertNotIn("pgvector", sql.lower())

    def test_render_news_rss_local_chunk_index_sql_rejects_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            render_news_rss_local_chunk_index_sql(document_limit=0)
        with self.assertRaises(ValueError):
            render_news_rss_local_chunk_index_sql(embedding_dimension=0)
        with self.assertRaises(ValueError):
            render_news_rss_local_chunk_index_sql(provider=" ")
        with self.assertRaises(ValueError):
            render_news_rss_local_chunk_index_sql(model_name="")

    def test_run_news_rss_local_chunk_index_records_pipeline_run(self) -> None:
        executor = FakeExecutor(run_id=777)
        summary = run_news_rss_local_chunk_index(
            config=type("Config", (), {})(),
            document_limit=25,
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 777)
        self.assertEqual(summary["status"], "completed")
        self.assertEqual(summary["chunk_count"], 2)
        self.assertEqual(summary["embedding_count"], 2)
        self.assertFalse(summary["external_embedding_api"])
        self.assertFalse(summary["live_llm_call"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("'ai'", executor.scalar_sql[0])
        self.assertIn("news_rss_local_chunk_index", executor.scalar_sql[0])
        self.assertIn("insert into ai.document_chunk", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_news_rss_local_chunk_index_marks_failed_when_index_errors(self) -> None:
        executor = FakeExecutor(run_id=778, fail_on_index=True)
        with self.assertRaises(RuntimeError):
            run_news_rss_local_chunk_index(
                config=type("Config", (), {})(),
                document_limit=25,
                executor=executor,
            )

        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])
        self.assertIn("boom", executor.non_query_sql[0])


if __name__ == "__main__":
    unittest.main()
