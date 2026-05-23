from __future__ import annotations

import json
import os
import subprocess
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ingest.news.ai_extract import (
    NewsAiImpactOutput,
    NewsAiOutput,
    NewsAiProviderResponse,
    NewsAiDocumentChunk,
    _diagnostic_excerpt,
    build_codex_oauth_news_ai_prompt,
    build_codex_oauth_news_ai_output_schema,
    build_news_ai_provider_response_from_payload,
    invoke_codex_oauth_news_ai_provider,
    is_news_ai_candidate_quality_eligible,
    load_news_rss_ai_extraction_candidates,
    parse_news_ai_output,
    run_news_rss_ai_extract,
    validate_news_ai_output,
)
from stockanalysis.ingest.news.models import NewsRssAiExtractionCandidate
from stockanalysis.ingest.news.sql import (
    REJECTED_NEWS_AI_ARTIFACT_TYPE,
    render_classification_node_lookup_by_code_sql,
    render_existing_news_ai_candidate_artifact_lookup_sql,
    render_news_ai_extraction_artifact_insert_sql,
    render_news_rss_ai_extraction_candidates_sql,
    render_news_rss_ai_retrieval_context_sql,
)
from stockanalysis.ingest.psql import PsqlExecutionError


class FakeExecutor:
    def __init__(self, *, existing_artifact_id: int | None = None) -> None:
        self.existing_artifact_id = existing_artifact_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.next_invocation_id = 9101
        self.next_artifact_id = 9201
        self.candidates = [
            {
                "event_id": 101,
                "document_id": 501,
                "title": "Nvidia H200 China deal survived the summit",
                "summary": "GPU export path stays open.",
                "event_at": "2026-05-19T10:02:40+00:00",
                "source_name": "rss_news:ai-semiconductor-cycle",
                "external_document_id": "rss:ai-semiconductor-cycle:abc",
                "source_url": "https://example.test/nvda",
                "existing_theme_code": "AI_SEMICONDUCTOR_CYCLE",
                "existing_instrument_symbol": "NVDA",
            }
        ]

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "json_agg(" in sql and "'existing_theme_code'" in sql:
            return json.dumps(self.candidates)
        if "'known_themes'" in sql:
            return json.dumps(
                {
                    "as_of_date": "2026-05-19",
                    "known_themes": [
                        {
                            "code": "AI_SEMICONDUCTOR_CYCLE",
                            "node_type": "subtheme",
                            "name": "AI Semiconductor Cycle",
                            "description": "AI accelerator and GPU cycle.",
                        }
                    ],
                    "theme_edges": [],
                    "current_event_impacts": [{"theme_code": "AI_SEMICONDUCTOR_CYCLE", "symbol": "NVDA"}],
                    "recent_similar_events": [],
                }
            )
        if "insert into ops.pipeline_run" in sql:
            return "8001"
        if "insert into ai.prompt_template" in sql:
            return "3001"
        if "from ai.extraction_artifact artifact" in sql and "news_event_candidate" in sql:
            if self.existing_artifact_id is None:
                raise PsqlExecutionError("psql returned no rows for scalar query")
            return str(self.existing_artifact_id)
        if "insert into ai.document_chunk" in sql:
            return "4001"
        if "insert into ai.model_invocation" in sql:
            invocation_id = self.next_invocation_id
            self.next_invocation_id += 1
            return str(invocation_id)
        if "insert into ai.extraction_artifact" in sql:
            artifact_id = self.next_artifact_id
            self.next_artifact_id += 1
            return str(artifact_id)
        if "from ref.classification_node node" in sql:
            node_rows = {
                "AI_SEMICONDUCTOR_CYCLE": {
                    "node_id": 21,
                    "code": "AI_SEMICONDUCTOR_CYCLE",
                    "node_type": "subtheme",
                    "name": "AI Semiconductor Cycle",
                },
                "MACRO_RATES_FED": {
                    "node_id": 22,
                    "code": "MACRO_RATES_FED",
                    "node_type": "subtheme",
                    "name": "Macro Rates and Fed",
                },
                "TECH_DOMAIN": {
                    "node_id": 23,
                    "code": "TECH_DOMAIN",
                    "node_type": "domain",
                    "name": "Technology Domain",
                },
            }
            for code, row in node_rows.items():
                if code in sql:
                    return json.dumps(row)
            else:
                raise PsqlExecutionError("psql returned no rows for scalar query")
        if "from ref.instrument i" in sql:
            if "NVDA" in sql:
                return json.dumps(
                    {
                        "instrument_id": 701,
                        "primary_symbol": "NVDA",
                        "instrument_name": "NVIDIA Corp",
                    }
                )
            if "XOM" in sql:
                return json.dumps(
                    {
                        "instrument_id": 702,
                        "primary_symbol": "XOM",
                        "instrument_name": "Exxon Mobil Corporation",
                    }
                )
            else:
                raise PsqlExecutionError("psql returned no rows for scalar query")
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class NewsRssAiExtractTests(unittest.TestCase):
    def test_render_news_ai_candidate_sql_excludes_existing_artifacts(self) -> None:
        sql = render_news_rss_ai_extraction_candidates_sql(as_of_date=date(2026, 5, 19), limit=10)

        self.assertIn("artifact.artifact_type in ('news_event_candidate', 'news_event_candidate_rejected')", sql)
        self.assertIn("d.document_type = 'news_rss_item'", sql)
        self.assertIn("rss_news:marketwatch-topstories", sql)
        self.assertIn("rss_news:yahoo-finance-news", sql)
        self.assertIn("US_MARKET_BREADTH", sql)
        self.assertIn("instrument.primary_symbol is null", sql)
        self.assertIn("limit 10", sql)

    def test_render_news_ai_candidate_sql_can_scope_existing_artifacts_to_prompt_version(self) -> None:
        sql = render_news_rss_ai_extraction_candidates_sql(
            as_of_date=date(2026, 5, 19),
            limit=10,
            prompt_template_name="news-rss-ai-extract",
            prompt_template_version="2026-05-21-ko-v2",
        )

        self.assertIn("join ai.prompt_template prompt", sql)
        self.assertIn("prompt.template_name = 'news-rss-ai-extract'", sql)
        self.assertIn("prompt.template_version = '2026-05-21-ko-v2'", sql)

    def test_render_news_ai_candidate_sql_picks_one_existing_theme_and_symbol_per_event(self) -> None:
        sql = render_news_rss_ai_extraction_candidates_sql(as_of_date=date(2026, 5, 19), limit=10)

        self.assertIn("left join lateral", sql)
        self.assertIn("limit 1", sql)
        self.assertIn("order by classification_impact.confidence desc nulls last", sql)
        self.assertIn("order by instrument_impact.confidence desc nulls last", sql)
        self.assertNotIn("left join event.event_classification_impact classification_impact\n      on", sql)
        self.assertNotIn("left join event.event_instrument_impact instrument_impact\n      on", sql)

    def test_render_news_ai_context_sql_uses_ontology_lite_tables(self) -> None:
        sql = render_news_rss_ai_retrieval_context_sql(event_id=101, as_of_date=date(2026, 5, 19))

        self.assertIn("ref.classification_node", sql)
        self.assertIn("ref.classification_edge", sql)
        self.assertIn("recent_similar_events", sql)

    def test_candidate_quality_gate_rejects_no_symbol_marketwatch_topstory(self) -> None:
        candidate = NewsRssAiExtractionCandidate(
            event_id=102,
            document_id=502,
            title="I inherited a house. Should I sell?",
            summary="Personal finance advice column.",
            event_at="2026-05-19T10:02:40+00:00",
            source_name="rss_news:marketwatch-topstories",
            external_document_id="rss:marketwatch-topstories:abc",
            source_url="https://www.marketwatch.com/story/personal-finance",
            existing_theme_code="MARKET_NEWS_FLOW",
            existing_instrument_symbol=None,
        )

        self.assertFalse(is_news_ai_candidate_quality_eligible(candidate))

    def test_candidate_quality_gate_allows_official_macro_without_symbol(self) -> None:
        candidate = NewsRssAiExtractionCandidate(
            event_id=103,
            document_id=503,
            title="Minutes of the Federal Open Market Committee",
            summary="FOMC minutes summarize inflation and rate risks.",
            event_at="2026-05-19T10:02:40+00:00",
            source_name="rss_news:macro-fed-press",
            external_document_id="rss:macro-fed-press:abc",
            source_url="https://www.federalreserve.gov/newsevents/pressreleases.htm",
            existing_theme_code="MACRO_RATES_FED",
            existing_instrument_symbol=None,
        )

        self.assertTrue(is_news_ai_candidate_quality_eligible(candidate))

    def test_candidate_quality_gate_rejects_no_symbol_yahoo_broad_theme(self) -> None:
        candidate = NewsRssAiExtractionCandidate(
            event_id=104,
            document_id=504,
            title="Trucking safety grants are available",
            summary="General funding advice for operators.",
            event_at="2026-05-19T10:02:40+00:00",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:yahoo-finance-news:abc",
            source_url="https://finance.yahoo.com/news/trucking-safety",
            existing_theme_code="MARKET_NEWS_FLOW",
            existing_instrument_symbol=None,
        )

        self.assertFalse(is_news_ai_candidate_quality_eligible(candidate))

    def test_candidate_quality_gate_allows_yahoo_with_symbol(self) -> None:
        candidate = NewsRssAiExtractionCandidate(
            event_id=105,
            document_id=505,
            title="NVIDIA posts blowout quarter",
            summary="AI demand lifts guidance.",
            event_at="2026-05-19T10:02:40+00:00",
            source_name="rss_news:yahoo-finance-news",
            external_document_id="rss:yahoo-finance-news:def",
            source_url="https://finance.yahoo.com/news/nvidia",
            existing_theme_code="AI_SEMICONDUCTOR_CYCLE",
            existing_instrument_symbol="NVDA",
        )

        self.assertTrue(is_news_ai_candidate_quality_eligible(candidate))

    def test_load_candidates_filters_no_symbol_marketwatch_topstories(self) -> None:
        executor = FakeExecutor()
        executor.candidates = [
            {
                "event_id": 102,
                "document_id": 502,
                "title": "I inherited a house. Should I sell?",
                "summary": "Personal finance advice column.",
                "event_at": "2026-05-19T10:02:40+00:00",
                "source_name": "rss_news:marketwatch-topstories",
                "external_document_id": "rss:marketwatch-topstories:abc",
                "source_url": "https://www.marketwatch.com/story/personal-finance",
                "existing_theme_code": "MARKET_NEWS_FLOW",
                "existing_instrument_symbol": None,
            },
            {
                "event_id": 103,
                "document_id": 503,
                "title": "Minutes of the Federal Open Market Committee",
                "summary": "FOMC minutes summarize inflation and rate risks.",
                "event_at": "2026-05-19T10:02:40+00:00",
                "source_name": "rss_news:macro-fed-press",
                "external_document_id": "rss:macro-fed-press:abc",
                "source_url": "https://www.federalreserve.gov/newsevents/pressreleases.htm",
                "existing_theme_code": "MACRO_RATES_FED",
                "existing_instrument_symbol": None,
            },
        ]

        candidates = load_news_rss_ai_extraction_candidates(
            as_of_date=date(2026, 5, 19),
            limit=10,
            executor=executor,
        )

        self.assertEqual([candidate.event_id for candidate in candidates], [103])

    def test_codex_oauth_prompt_requires_korean_human_readable_fields(self) -> None:
        prompt = build_codex_oauth_news_ai_prompt(
            NewsRssAiExtractionCandidate(
                event_id=101,
                document_id=501,
                title="Treasury yields spike",
                summary="S&P 500 pressure follows rate shock.",
                event_at="2026-05-19T10:02:40+00:00",
                source_name="rss_news:macro",
                external_document_id="rss:macro:abc",
                source_url="https://example.test/macro",
                existing_theme_code="MACRO_RATES_FED",
                existing_instrument_symbol="SPY",
            ),
            NewsAiDocumentChunk(
                document_id=501,
                chunk_index=9000,
                content_hash="hash",
                text_preview="Treasury yields spike",
                token_count=12,
                chunk_metadata={"source": "rss"},
                text="Title: Treasury yields spike\nSummary: S&P 500 pressure follows rate shock.",
            ),
            {
                "known_themes": [{"code": "MACRO_RATES_FED"}],
                "theme_edges": [],
                "current_event_impacts": [{"symbol": "SPY", "theme_code": "MACRO_RATES_FED"}],
                "recent_similar_events": [],
            },
        )

        self.assertIn("Write all human-readable natural-language fields in Korean.", prompt)
        self.assertIn("event_summary, rationale, evidence_summary, uncertainty_notes, causal_paths rationale", prompt)
        self.assertIn("Separate impacts into macro_regime_impacts, domain_impacts, theme_impacts", prompt)
        self.assertIn("Do not force macro or domain news onto a stock", prompt)
        self.assertIn("Keep machine codes and market identifiers unchanged", prompt)

    def test_codex_oauth_output_schema_requires_hierarchical_fields(self) -> None:
        schema = build_codex_oauth_news_ai_output_schema()
        candidate_schema = schema["properties"]["candidate"]

        self.assertIn("macro_regime_impacts", candidate_schema["required"])
        self.assertIn("domain_impacts", candidate_schema["required"])
        self.assertIn("direct_instrument_impacts", candidate_schema["required"])
        self.assertIn("causal_paths", candidate_schema["required"])
        self.assertIn("evidence_spans", candidate_schema["required"])
        self.assertNotIn("instrument_impacts", candidate_schema["required"])

    def test_codex_oauth_invocation_uses_safe_automation_workdir_and_git_skip(self) -> None:
        candidate = NewsRssAiExtractionCandidate(
            event_id=101,
            document_id=501,
            title="Nvidia H200 China deal survived the summit",
            summary="GPU export path stays open.",
            event_at="2026-05-19T10:02:40+00:00",
            source_name="rss_news:ai-semiconductor-cycle",
            external_document_id="rss:ai-semiconductor-cycle:abc",
            source_url="https://example.test/nvda",
            existing_theme_code="AI_SEMICONDUCTOR_CYCLE",
            existing_instrument_symbol="NVDA",
        )
        chunk = NewsAiDocumentChunk(
            document_id=501,
            chunk_index=9000,
            content_hash="abc",
            text_preview="Nvidia H200 China deal survived the summit",
            token_count=10,
            chunk_metadata={},
            text="Nvidia H200 China deal survived the summit",
        )
        fixture_output = Path("tests/fixtures/llm_news_event_candidate_nvda.json").read_text(encoding="utf-8")

        with patch.dict(
            os.environ,
            {
                "STOCKANALYSIS_CODEX_CLI_COMMAND": "codex",
                "STOCKANALYSIS_CODEX_SKIP_GIT_REPO_CHECK": "1",
            },
            clear=False,
        ):
            with patch("stockanalysis.ingest.news.ai_extract.subprocess.run") as run_mock:
                run_mock.return_value = subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=fixture_output,
                    stderr="",
                )
                response = invoke_codex_oauth_news_ai_provider(
                    candidate,
                    chunk,
                    {
                        "known_themes": [],
                        "theme_edges": [],
                        "current_event_impacts": [],
                        "recent_similar_events": [],
                    },
                    "codex-cli-default",
                    "low",
                )

        command = run_mock.call_args.args[0]
        self.assertEqual(response.provider, "codex_oauth")
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("--cd", command)
        self.assertTrue(Path(command[command.index("--cd") + 1]).exists())
        self.assertLess(command.index("exec"), command.index("--skip-git-repo-check"))

    def test_diagnostic_excerpt_preserves_failure_tail(self) -> None:
        diagnostic = _diagnostic_excerpt(
            "prompt line\n" * 400 + "FINAL_ERROR: schema validation failed after model output",
            200,
        )

        self.assertTrue(diagnostic.startswith("...<truncated; showing diagnostic tail>"))
        self.assertIn("FINAL_ERROR: schema validation failed", diagnostic)
        self.assertLessEqual(len(diagnostic), 200)
        self.assertNotEqual(diagnostic, "prompt line\n" * 400)

    def test_render_lookup_and_artifact_sql(self) -> None:
        lookup_sql = render_classification_node_lookup_by_code_sql("AI_SEMICONDUCTOR_CYCLE")
        existing_sql = render_existing_news_ai_candidate_artifact_lookup_sql(event_id=101, request_hash="abc")
        artifact_sql = render_news_ai_extraction_artifact_insert_sql(
            invocation_id=1,
            document_id=2,
            event_id=3,
            output_json={"ok": True},
            confidence=0.8,
        )

        self.assertIn("upper(node.code)", lookup_sql)
        self.assertIn("invocation.request_hash = 'abc'", existing_sql)
        self.assertIn("'news_event_candidate'", artifact_sql)

    def test_parse_and_validate_rejects_unknown_theme_and_symbol(self) -> None:
        payload = json.loads(Path("tests/fixtures/llm_news_event_candidate_nvda.json").read_text(encoding="utf-8"))
        response = build_news_ai_provider_response_from_payload(
            payload,
            provider="fixture",
            model_name="news-fixture-v1",
            reasoning_effort="none",
        )

        validated = validate_news_ai_output(response.output, min_confidence=0.72, executor=FakeExecutor())

        self.assertEqual(len(validated.theme_impacts), 1)
        self.assertEqual(len(validated.instrument_impacts), 1)
        self.assertEqual(validated.rejected_impact_count, 2)
        self.assertEqual(validated.theme_impacts[0].node_code, "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(validated.instrument_impacts[0].primary_symbol, "NVDA")

    def test_validate_rejects_direct_instrument_not_named_in_source_text(self) -> None:
        output = parse_news_ai_output(
            {
                "analysis_method": "codex_oauth_hierarchical_v3",
                "event_summary": "AI가 고용시장에 미칠 영향을 다룬 뉴스다.",
                "macro_regime_impacts": [],
                "domain_impacts": [],
                "theme_impacts": [
                    {
                        "node_code": "AI_SEMICONDUCTOR_CYCLE",
                        "impact_direction": "watch",
                        "impact_strength": 0.58,
                        "confidence": 0.82,
                        "rationale": "AI 인프라 논점이 포함됐다.",
                        "evidence_summary": "AI worries are discussed.",
                    }
                ],
                "direct_instrument_impacts": [
                    {
                        "symbol": "XOM",
                        "impact_direction": "supportive",
                        "impact_strength": 0.55,
                        "confidence": 0.86,
                        "rationale": "모델이 잘못 연결한 직접 종목이다.",
                        "evidence_summary": "기사 본문에는 Exxon 또는 XOM이 없다.",
                    }
                ],
                "causal_paths": [],
                "uncertainty_notes": "직접 기업명이 없는 기사다.",
                "evidence_spans": [],
                "recommendation_relevance": "watchlist",
            }
        )

        validated = validate_news_ai_output(
            output,
            min_confidence=0.72,
            executor=FakeExecutor(),
            source_text="Artificial intelligence has Americans worried about jobs. Now there is a new AI worry.",
        )

        self.assertEqual(len(validated.theme_impacts), 1)
        self.assertEqual(len(validated.instrument_impacts), 0)
        self.assertEqual(validated.rejected_impact_count, 1)

    def test_parse_and_validate_hierarchical_macro_only_output(self) -> None:
        output = parse_news_ai_output(
            {
                "analysis_method": "codex_oauth_hierarchical_v3",
                "event_summary": "연준 금리 경로가 성장주 할인율 부담을 키운 뉴스다.",
                "macro_regime_impacts": [
                    {
                        "node_code": "MACRO_RATES_FED",
                        "impact_direction": "risk_review",
                        "impact_strength": 0.82,
                        "confidence": 0.88,
                        "rationale": "금리 경로가 직접 언급됐다.",
                        "evidence_summary": "연준과 국채금리 상승 압력이 핵심 근거다.",
                    }
                ],
                "domain_impacts": [
                    {
                        "node_code": "TECH_DOMAIN",
                        "impact_direction": "risk_review",
                        "impact_strength": 0.64,
                        "confidence": 0.8,
                        "rationale": "기술주는 할인율 상승에 민감하다.",
                        "evidence_summary": "성장주 밸류에이션 부담이 연결 근거다.",
                    }
                ],
                "theme_impacts": [],
                "direct_instrument_impacts": [],
                "causal_paths": [
                    {
                        "path": ["MACRO_RATES_FED", "TECH_DOMAIN"],
                        "confidence": 0.78,
                        "rationale": "금리 충격이 기술 도메인으로 전파된다.",
                    }
                ],
                "uncertainty_notes": "개별 기업 뉴스가 아니므로 직접 종목 연결은 제외했다.",
                "evidence_spans": [
                    {
                        "span_text": "Treasury yields spike after Fed comments",
                        "supports": ["MACRO_RATES_FED"],
                    }
                ],
                "recommendation_relevance": "보유 기술주 리스크 검토 입력으로만 사용한다.",
            }
        )

        validated = validate_news_ai_output(output, min_confidence=0.72, executor=FakeExecutor())

        self.assertEqual(len(validated.theme_impacts), 2)
        self.assertEqual(len(validated.instrument_impacts), 0)
        self.assertEqual(validated.rejected_impact_count, 0)
        self.assertEqual(validated.theme_impacts[0].node_code, "MACRO_RATES_FED")
        self.assertEqual(output.causal_paths[0].path, ("MACRO_RATES_FED", "TECH_DOMAIN"))
        self.assertEqual(output.evidence_spans[0].supports, ("MACRO_RATES_FED",))

    def test_validate_rejects_low_confidence(self) -> None:
        output = parse_news_ai_output(
            {
                "analysis_method": "fixture",
                "event_summary": "summary",
                "theme_impacts": [
                    {
                        "theme_code": "AI_SEMICONDUCTOR_CYCLE",
                        "impact_direction": "supportive",
                        "impact_strength": 0.6,
                        "confidence": 0.4,
                        "rationale": "too low",
                        "evidence_summary": "too low",
                    }
                ],
                "instrument_impacts": [],
                "uncertainty_notes": "low confidence",
                "recommendation_relevance": "watchlist",
            }
        )

        validated = validate_news_ai_output(output, min_confidence=0.72, executor=FakeExecutor())

        self.assertEqual(len(validated.theme_impacts), 0)
        self.assertEqual(validated.rejected_impact_count, 1)

    def test_run_news_ai_extract_dry_run_does_not_write_or_call_provider(self) -> None:
        executor = FakeExecutor()
        summary = run_news_rss_ai_extract(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            limit=10,
            provider="codex_oauth",
            execute=False,
            executor=executor,
            provider_runner=lambda *_args: (_ for _ in ()).throw(AssertionError("provider called")),
        )

        self.assertEqual(summary["status"], "planned")
        self.assertEqual(summary["planned_event_count"], 1)
        self.assertEqual(executor.non_query_sql, [])
        self.assertFalse(any("insert into ops.pipeline_run" in sql for sql in executor.scalar_sql))

    def test_run_news_ai_extract_fixture_writes_artifact_and_validated_impacts(self) -> None:
        executor = FakeExecutor()
        summary = run_news_rss_ai_extract(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            limit=10,
            provider="fixture",
            model_name="news-fixture-v1",
            reasoning_effort="none",
            execute=True,
            llm_output_json_path="tests/fixtures/llm_news_event_candidate_nvda.json",
            executor=executor,
        )

        self.assertEqual(summary["run_id"], 8001)
        self.assertEqual(summary["pipeline_name"], "event_intelligence_llm_extract")
        self.assertEqual(summary["inserted_artifact_count"], 1)
        self.assertEqual(summary["validated_theme_impact_count"], 1)
        self.assertEqual(summary["validated_instrument_impact_count"], 1)
        self.assertEqual(summary["rejected_impact_count"], 2)
        self.assertTrue(any("'news_event_candidate'" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("extracted_fields" in sql for sql in executor.scalar_sql))
        self.assertTrue(any("insert into event.event_classification_impact" in sql for sql in executor.non_query_sql))
        self.assertTrue(any("insert into event.event_instrument_impact" in sql for sql in executor.non_query_sql))
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])

    def test_run_news_ai_extract_rejects_artifact_without_validated_impacts(self) -> None:
        executor = FakeExecutor()

        def low_confidence_provider(*_args):
            return NewsAiProviderResponse(
                provider="fixture",
                model_name="news-fixture-v1",
                reasoning_effort="none",
                output=NewsAiOutput(
                    analysis_method="fixture",
                    event_summary="Low-confidence broad market note.",
                    theme_impacts=(
                        NewsAiImpactOutput(
                            target="AI_SEMICONDUCTOR_CYCLE",
                            impact_direction="watch",
                            impact_strength=0.4,
                            confidence=0.3,
                            rationale="Weak evidence.",
                            evidence_summary="No validated impact.",
                        ),
                    ),
                    instrument_impacts=(),
                    uncertainty_notes="Too weak for accepted candidate.",
                    recommendation_relevance="low",
                ),
                input_token_count=10,
                output_token_count=20,
                cached_input_token_count=0,
                estimated_cost_usd=None,
                latency_ms=1,
            )

        summary = run_news_rss_ai_extract(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            limit=10,
            provider="fixture",
            model_name="news-fixture-v1",
            reasoning_effort="none",
            execute=True,
            llm_output_json_path="tests/fixtures/llm_news_event_candidate_nvda.json",
            executor=executor,
            provider_runner=low_confidence_provider,
        )

        self.assertEqual(summary["inserted_artifact_count"], 0)
        self.assertEqual(summary["rejected_candidate_count"], 1)
        self.assertEqual(summary["results"][0]["status"], "rejected_no_validated_impacts")
        self.assertTrue(any(REJECTED_NEWS_AI_ARTIFACT_TYPE in sql for sql in executor.scalar_sql))
        self.assertFalse(any("insert into event.event_classification_impact" in sql for sql in executor.non_query_sql))

    def test_run_news_ai_extract_marks_fallback_status_when_provider_fails(self) -> None:
        executor = FakeExecutor()

        summary = run_news_rss_ai_extract(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            limit=10,
            provider="codex_oauth",
            execute=True,
            executor=executor,
            provider_runner=lambda *_args: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
        )

        self.assertEqual(summary["status"], "completed_with_fallback")
        self.assertEqual(summary["failed_candidate_count"], 1)
        self.assertEqual(summary["inserted_artifact_count"], 0)
        self.assertTrue(
            any("status = 'succeeded_with_fallback'" in sql for sql in executor.non_query_sql),
            executor.non_query_sql,
        )
        self.assertTrue(
            any("review ai.model_invocation errors" in sql for sql in executor.non_query_sql),
            executor.non_query_sql,
        )

    def test_run_news_ai_extract_skips_existing_request_hash(self) -> None:
        executor = FakeExecutor(existing_artifact_id=9901)
        summary = run_news_rss_ai_extract(
            config=type("Config", (), {})(),
            as_of_date=date(2026, 5, 19),
            limit=10,
            provider="fixture",
            model_name="news-fixture-v1",
            reasoning_effort="none",
            execute=True,
            llm_output_json_path="tests/fixtures/llm_news_event_candidate_nvda.json",
            executor=executor,
        )

        self.assertEqual(summary["inserted_artifact_count"], 0)
        self.assertEqual(summary["skipped_existing_count"], 1)
        self.assertFalse(any("insert into ai.extraction_artifact" in sql for sql in executor.scalar_sql))


if __name__ == "__main__":
    unittest.main()
