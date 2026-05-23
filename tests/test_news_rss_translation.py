from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.news.sql import (
    render_news_rss_translation_candidates_sql,
    render_source_document_translation_update_sql,
)
from stockanalysis.ingest.news.translation import (
    CODEX_OAUTH_PROVIDER,
    NewsRssTranslationCandidate,
    NewsTranslationOutput,
    NewsTranslationProviderResponse,
    build_codex_oauth_news_translation_output_schema,
    build_codex_oauth_news_translation_prompt,
    build_news_translation_provider_response_from_payload,
    parse_news_translation_output,
    run_news_rss_translation,
)


class FakeTranslationExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from ingest.source_document d" in sql and "korean_title" in sql:
            return json.dumps(
                [
                    {
                        "event_id": 101,
                        "document_id": 501,
                        "title": "Quantum stocks soar as the Trump administration looks to be buying in",
                        "summary": "Quantum-computing shares rallied after a policy report.",
                        "published_at": "2026-05-22T20:33:00+00:00",
                        "source_name": "rss_news:yahoo-finance-news",
                        "external_document_id": "rss:yahoo-finance-news:quantum",
                        "source_url": "https://example.test/quantum",
                        "existing_theme_code": "QUANTUM_COMPUTING_POLICY",
                        "existing_instrument_symbol": None,
                        "impact_direction": "supportive",
                        "impact_score": 0.68,
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return "8001"
        if "insert into ai.prompt_template" in sql:
            return "3001"
        if "insert into ai.model_invocation" in sql:
            return "9101"
        if "update ingest.source_document" in sql:
            return "501"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class NewsRssTranslationTests(unittest.TestCase):
    def test_render_translation_candidate_sql_selects_untranslated_rss_documents(self) -> None:
        sql = render_news_rss_translation_candidates_sql(as_of_date=date(2026, 5, 23), limit=20)

        self.assertIn("d.document_type = 'news_rss_item'", sql)
        self.assertIn("d.korean_title is null", sql)
        self.assertIn("'korean_summary', korean_summary", sql)
        self.assertIn("limit 20", sql)

    def test_render_source_document_translation_update_sql_persists_invocation_trace(self) -> None:
        sql = render_source_document_translation_update_sql(
            document_id=501,
            korean_title="트럼프 행정부 매입 기대에 양자컴퓨터 주식이 급등했다",
            korean_summary="양자컴퓨팅 관련주가 정책 기대감에 상승했다.",
            translation_confidence=0.91,
            translation_provider=CODEX_OAUTH_PROVIDER,
            translation_model_name="codex-cli-default",
            translation_invocation_id=9101,
        )

        self.assertIn("korean_title =", sql)
        self.assertIn("korean_summary =", sql)
        self.assertIn("translation_confidence = 0.9100::numeric", sql)
        self.assertIn("translation_invocation_id = 9101::bigint", sql)

    def test_parse_translation_output_requires_bounded_confidence(self) -> None:
        output = parse_news_translation_output(
            {
                "korean_title": "트럼프 행정부 매입 기대에 양자컴퓨터 주식이 급등했다",
                "korean_summary": "양자컴퓨팅 관련주가 정책 기대감에 상승했다.",
                "translation_confidence": 0.91,
            }
        )

        self.assertEqual(output.korean_title, "트럼프 행정부 매입 기대에 양자컴퓨터 주식이 급등했다")
        self.assertEqual(output.translation_confidence, 0.91)

        with self.assertRaises(ValueError):
            parse_news_translation_output(
                {
                    "korean_title": "제목",
                    "korean_summary": "요약",
                    "translation_confidence": 1.5,
                }
            )

    def test_codex_translation_prompt_and_schema_are_korean_first(self) -> None:
        candidate = _candidate()
        prompt = build_codex_oauth_news_translation_prompt(candidate, "Title: Quantum stocks soar")
        schema = build_codex_oauth_news_translation_output_schema()

        self.assertIn("natural Korean sentence-level wording", prompt)
        self.assertIn("Do not browse", prompt)
        self.assertIn("Do not replace the title with a generic label", prompt)
        self.assertEqual(schema["required"], ["translation"])
        self.assertIn("korean_title", json.dumps(schema))
        self.assertIn("translation_confidence", json.dumps(schema))

    def test_build_provider_response_accepts_translation_wrapper(self) -> None:
        response = build_news_translation_provider_response_from_payload(
            {
                "translation": {
                    "korean_title": "트럼프 행정부 매입 기대에 양자컴퓨터 주식이 급등했다",
                    "korean_summary": "양자컴퓨팅 관련주가 정책 기대감에 상승했다.",
                    "translation_confidence": 0.91,
                },
                "usage": {"input_tokens": 12, "output_tokens": 20},
            },
            provider=CODEX_OAUTH_PROVIDER,
            model_name="codex-cli-default",
            reasoning_effort="low",
        )

        self.assertEqual(response.output.korean_title, "트럼프 행정부 매입 기대에 양자컴퓨터 주식이 급등했다")
        self.assertEqual(response.input_token_count, 12)

    def test_run_translation_execute_updates_source_document_and_records_invocation(self) -> None:
        executor = FakeTranslationExecutor()

        def provider_runner(candidate, bounded_text, model_name, reasoning_effort):
            self.assertEqual(candidate.document_id, 501)
            self.assertIn("Quantum stocks", bounded_text)
            return NewsTranslationProviderResponse(
                provider=CODEX_OAUTH_PROVIDER,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                output=NewsTranslationOutput(
                    korean_title="트럼프 행정부 매입 기대에 양자컴퓨터 주식이 급등했다",
                    korean_summary="양자컴퓨팅 관련주가 정책 기대감에 상승했다.",
                    translation_confidence=0.91,
                ),
                input_token_count=12,
                output_token_count=20,
                cached_input_token_count=None,
                estimated_cost_usd=None,
                latency_ms=1234,
            )

        report = run_news_rss_translation(
            config=RuntimeConfig(psql_command="unused"),
            as_of_date=date(2026, 5, 23),
            limit=1,
            provider=CODEX_OAUTH_PROVIDER,
            execute=True,
            executor=executor,
            provider_runner=provider_runner,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["updated_document_count"], 1)
        self.assertTrue(any("insert into ai.model_invocation" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("update ingest.source_document" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("status = 'succeeded'" in sql for sql in executor.non_query_sql))


def _candidate() -> NewsRssTranslationCandidate:
    return NewsRssTranslationCandidate(
        event_id=101,
        document_id=501,
        title="Quantum stocks soar as the Trump administration looks to be buying in",
        summary="Quantum-computing shares rallied after a policy report.",
        published_at="2026-05-22T20:33:00+00:00",
        source_name="rss_news:yahoo-finance-news",
        external_document_id="rss:yahoo-finance-news:quantum",
        source_url="https://example.test/quantum",
        existing_theme_code="QUANTUM_COMPUTING_POLICY",
        existing_instrument_symbol=None,
        impact_direction="supportive",
        impact_score=0.68,
    )


if __name__ == "__main__":
    unittest.main()
