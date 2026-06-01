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
    build_news_translation_input,
    parse_news_translation_output,
    run_news_rss_translation,
    validate_news_translation_output_grounding,
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
        self.assertIn("Do not introduce English company names", prompt)
        self.assertIn("Do not replace the title with a generic label", prompt)
        self.assertEqual(schema["required"], ["translation"])
        self.assertIn("korean_title", json.dumps(schema))
        self.assertIn("translation_confidence", json.dumps(schema))

    def test_validate_translation_output_rejects_ungrounded_english_entities(self) -> None:
        candidate = NewsRssTranslationCandidate(
            event_id=19,
            document_id=22,
            title="Dow Jones Futures: Trump Says Iran Deal Announcement 'Shortly' With Hormuz 'Opened'; Tesla, AI Stocks Near Buy Points",
            summary="RSS item without publisher summary.",
            published_at="2026-05-23T21:39:29+00:00",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:yahoo-finance-news:a9942e6ecc582301998de621",
            source_url="https://example.test/dow-jones-futures",
            existing_theme_code="MACRO_RATES_FED",
            existing_instrument_symbol="SPY",
            impact_direction="watch",
            impact_score=0.68,
        )
        bounded_text = build_news_translation_input(candidate, max_input_chars=4000)

        with self.assertRaisesRegex(ValueError, "spacex.*starlink"):
            validate_news_translation_output_grounding(
                candidate=candidate,
                bounded_text=bounded_text,
                output=NewsTranslationOutput(
                    korean_title="통신주: SpaceX IPO 서류가 드러낸 Starlink의 큰 야심",
                    korean_summary="SpaceX IPO 관련 공개 자료가 Starlink의 통신 시장 확장 야심을 드러냈다.",
                    translation_confidence=0.72,
                ),
            )

    def test_validate_translation_output_allows_grounded_english_entities(self) -> None:
        candidate = _candidate()
        bounded_text = build_news_translation_input(candidate, max_input_chars=4000)

        validate_news_translation_output_grounding(
            candidate=candidate,
            bounded_text=bounded_text,
            output=NewsTranslationOutput(
                korean_title="Trump 행정부 매입 기대에 Quantum 주식이 급등했다",
                korean_summary="Quantum-computing 주식이 정책 보고서 이후 상승했다.",
                translation_confidence=0.91,
            ),
        )

    def test_validate_translation_output_allows_source_token_aliases(self) -> None:
        candidate = NewsRssTranslationCandidate(
            event_id=21,
            document_id=33,
            title="Stocks edge higher as investors parse ETF inflows",
            summary="RSS item without publisher summary.",
            published_at="2026-06-01T01:30:00+00:00",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:yahoo-finance-news:abc123",
            source_url="https://finance.yahoo.com/news/stocks-etfs",
            existing_theme_code="MACRO_LIQUIDITY",
            existing_instrument_symbol=None,
            impact_direction="watch",
            impact_score=0.62,
        )
        bounded_text = build_news_translation_input(candidate, max_input_chars=4000)

        validate_news_translation_output_grounding(
            candidate=candidate,
            bounded_text=bounded_text,
            output=NewsTranslationOutput(
                korean_title="Yahoo Finance: ETF 자금 유입을 보며 주식이 소폭 상승했다",
                korean_summary="Yahoo Finance 원문은 투자자들이 ETF 유입을 해석하는 가운데 시장이 상승했다고 전했다.",
                translation_confidence=0.88,
            ),
        )

    def test_validate_translation_output_allows_common_market_abbreviations(self) -> None:
        candidate = NewsRssTranslationCandidate(
            event_id=22,
            document_id=34,
            title="Crypto-linked stocks climb as digital asset optimism returns",
            summary="Cryptocurrency exposed equities gained in early trading.",
            published_at="2026-06-01T01:40:00+00:00",
            source_name="rss_news:marketwatch",
            external_document_id="rss:marketwatch:def456",
            source_url="https://www.marketwatch.com/story/crypto-linked-stocks",
            existing_theme_code="TECH_DOMAIN",
            existing_instrument_symbol=None,
            impact_direction="supportive",
            impact_score=0.64,
        )
        bounded_text = build_news_translation_input(candidate, max_input_chars=4000)

        validate_news_translation_output_grounding(
            candidate=candidate,
            bounded_text=bounded_text,
            output=NewsTranslationOutput(
                korean_title="MarketWatch: crypto 관련 주식이 디지털 자산 기대감에 올랐다",
                korean_summary="MarketWatch 원문은 cryptocurrency 노출 주식이 상승했다고 전했다.",
                translation_confidence=0.87,
            ),
        )

    def test_validate_translation_output_allows_grounded_singularized_acronyms(self) -> None:
        candidate = NewsRssTranslationCandidate(
            event_id=23,
            document_id=35,
            title="Are Hot IPOs a Sign of a Market Top?",
            summary="A bank strategist says CDs and IPOs show investors are seeking alternatives.",
            published_at="2026-06-01T01:50:00+00:00",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:yahoo-finance-news:ghi789",
            source_url="https://finance.yahoo.com/news/hot-ipos",
            existing_theme_code="MARKET_NEWS_FLOW",
            existing_instrument_symbol=None,
            impact_direction="watch",
            impact_score=0.61,
        )
        bounded_text = build_news_translation_input(candidate, max_input_chars=4000)

        validate_news_translation_output_grounding(
            candidate=candidate,
            bounded_text=bounded_text,
            output=NewsTranslationOutput(
                korean_title="뜨거운 IPO가 시장 고점의 신호일까?",
                korean_summary="원문은 IPO와 CD 수요를 투자자 대안 선호의 단서로 다뤘다.",
                translation_confidence=0.88,
            ),
        )

    def test_validate_translation_output_allows_ai_when_openai_is_grounded(self) -> None:
        candidate = NewsRssTranslationCandidate(
            event_id=24,
            document_id=36,
            title="Anthropic nears $1 trillion valuation, leapfrogging OpenAI",
            summary="A funding round follows a revenue surge for the Claude creator.",
            published_at="2026-06-01T02:00:00+00:00",
            source_name="rss_news:marketwatch",
            external_document_id="rss:marketwatch:jkl012",
            source_url="https://www.marketwatch.com/story/anthropic-openai",
            existing_theme_code="AI_LABOR_PRODUCTIVITY",
            existing_instrument_symbol=None,
            impact_direction="supportive",
            impact_score=0.66,
        )
        bounded_text = build_news_translation_input(candidate, max_input_chars=4000)

        validate_news_translation_output_grounding(
            candidate=candidate,
            bounded_text=bounded_text,
            output=NewsTranslationOutput(
                korean_title="Anthropic이 OpenAI를 앞지르며 1조 달러 가치에 접근했다",
                korean_summary="AI 기업 가치평가 경쟁이 다시 부각됐다는 내용이다.",
                translation_confidence=0.9,
            ),
        )

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
