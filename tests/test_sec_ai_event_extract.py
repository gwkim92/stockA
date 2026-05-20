from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ingest.sec.ai_event_extract import (
    CODEX_OAUTH_PROVIDER,
    build_ai_document_chunk,
    build_codex_oauth_event_prompt,
    build_codex_oauth_output_schema,
    build_sec_event_candidate_from_structured_output,
    invoke_codex_oauth_structured_event_provider,
    load_structured_event_provider_response,
    render_ai_document_chunk_upsert_sql,
    render_ai_extraction_artifact_insert_sql,
    render_ai_model_invocation_insert_sql,
    render_ai_prompt_template_upsert_sql,
    run_event_intelligence_llm_extract,
)
from stockanalysis.ingest.sec.models import SecEventSourceDocumentRecord


FIXTURES_DIR = Path(__file__).parent / "fixtures"
LLM_FIXTURE = FIXTURES_DIR / "llm_sec_event_aapl_10k_structured.json"


class FakeAiEventExecutor:
    def __init__(self, *, run_id: int = 801, fail_on_event_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_event_upsert = fail_on_event_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.lookup_payload = {
            "document_id": 71,
            "external_document_id": "0000320193-24-000123",
            "title": "10-K - 10-K",
            "summary": "SEC 10-K filing for Apple Inc. | 10-K | file number: 001-36743",
            "published_at": "2024-11-01T00:00:00+00:00",
            "raw_storage_uri": (FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html").resolve().as_uri(),
            "checksum": "abc123",
        }

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from ingest.source_document" in sql:
            return json.dumps(self.lookup_payload)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.prompt_template" in sql:
            return "301"
        if "insert into ai.document_chunk" in sql:
            return "401"
        if "insert into ai.model_invocation" in sql:
            return "501"
        if "insert into ai.extraction_artifact" in sql:
            return "601"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_event_upsert and "insert into event.event" in sql:
            raise RuntimeError("event upsert failed")


class SecAiEventExtractTests(unittest.TestCase):
    def test_load_structured_event_provider_response(self) -> None:
        response = load_structured_event_provider_response(
            str(LLM_FIXTURE),
            provider="fixture",
            model_name="fallback-model",
            reasoning_effort="low",
        )
        self.assertEqual(response.provider, "fixture")
        self.assertEqual(response.model_name, "gpt-5.4-nano")
        self.assertEqual(response.input_token_count, 1450)
        self.assertEqual(response.cached_input_token_count, 900)
        self.assertEqual(response.event.event_type, "sec_annual_report_filed")
        self.assertEqual(response.event.confidence, 0.93)

    def test_codex_oauth_prompt_and_schema_do_not_expose_auth_files(self) -> None:
        record = _source_document_record()
        chunk = build_ai_document_chunk(record, max_input_chars=700)
        prompt = build_codex_oauth_event_prompt(record, chunk)
        schema = build_codex_oauth_output_schema()

        self.assertIn("Do not browse", prompt)
        self.assertIn("Bounded SEC filing context", prompt)
        self.assertNotIn("auth.json", prompt)
        self.assertIn("event", schema["properties"])
        self.assertIn("event", schema["required"])

    def test_invoke_codex_oauth_provider_uses_cli_boundary(self) -> None:
        record = _source_document_record()
        chunk = build_ai_document_chunk(record, max_input_chars=700)
        payload = {
            "provider": "codex_oauth",
            "model_name": "codex-cli-default",
            "reasoning_effort": "low",
            "event": json.loads(LLM_FIXTURE.read_text(encoding="utf-8"))["event"],
            "usage": {"output_tokens": 120},
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = Path(tmpdir) / "fake-codex.py"
            runner.write_text(
                "\n".join(
                    [
                        "import pathlib, sys",
                        "args = sys.argv[1:]",
                        "assert 'exec' in args",
                        "assert '--ephemeral' in args",
                        "assert '--sandbox' in args and 'read-only' in args",
                        "assert '--ask-for-approval' in args and 'never' in args",
                        "assert 'auth.json' not in ' '.join(args)",
                        "output = pathlib.Path(args[args.index('--output-last-message') + 1])",
                        f"output.write_text({json.dumps(json.dumps(payload))}, encoding='utf-8')",
                    ]
                ),
                encoding="utf-8",
            )
            command = f"{sys.executable} {runner}"
            with patch.dict("os.environ", {"STOCKANALYSIS_CODEX_CLI_COMMAND": command}):
                response = invoke_codex_oauth_structured_event_provider(
                    record,
                    chunk,
                    "codex-cli-default",
                    "low",
                )

        self.assertEqual(response.provider, CODEX_OAUTH_PROVIDER)
        self.assertEqual(response.model_name, "codex-cli-default")
        self.assertEqual(response.output_token_count, 120)

    def test_build_ai_document_chunk_limits_and_hashes_text(self) -> None:
        record = _source_document_record()
        chunk = build_ai_document_chunk(record, max_input_chars=700)
        self.assertEqual(chunk.document_id, 71)
        self.assertEqual(chunk.chunk_index, 0)
        self.assertEqual(len(chunk.content_hash), 64)
        self.assertLessEqual(len(chunk.text), 700)
        self.assertIn("Annual Report", chunk.text_preview)
        self.assertEqual(chunk.chunk_metadata["external_document_id"], "0000320193-24-000123")

    def test_build_sec_event_candidate_rejects_low_confidence(self) -> None:
        response = load_structured_event_provider_response(
            str(LLM_FIXTURE),
            provider="fixture",
            model_name="gpt-5.4-nano",
            reasoning_effort="low",
        )
        with self.assertRaisesRegex(ValueError, "below min_confidence"):
            build_sec_event_candidate_from_structured_output(
                _source_document_record(),
                response.event,
                min_confidence=0.95,
            )

    def test_render_ai_sql_fragments(self) -> None:
        chunk = build_ai_document_chunk(_source_document_record(), max_input_chars=700)
        prompt_sql = render_ai_prompt_template_upsert_sql()
        chunk_sql = render_ai_document_chunk_upsert_sql(chunk)
        invocation_sql = render_ai_model_invocation_insert_sql(
            run_id=801,
            task_name="event-intelligence-llm-extract",
            provider="fixture",
            model_name="gpt-5.4-nano",
            reasoning_effort="low",
            prompt_template_id=301,
            input_token_count=1450,
            output_token_count=180,
            cached_input_token_count=900,
            estimated_cost_usd=None,
            latency_ms=0,
            status="succeeded",
            error_summary=None,
            request_hash="abc123",
        )
        artifact_sql = render_ai_extraction_artifact_insert_sql(
            invocation_id=501,
            document_id=71,
            output_json={"event": {"event_type": "sec_annual_report_filed"}},
            confidence=0.93,
        )
        self.assertIn("insert into ai.prompt_template", prompt_sql)
        self.assertIn("event-intelligence-llm-extract", prompt_sql)
        self.assertIn("insert into ai.document_chunk", chunk_sql)
        self.assertIn(chunk.content_hash, chunk_sql)
        self.assertIn("insert into ai.model_invocation", invocation_sql)
        self.assertIn("cached_input_token_count", invocation_sql)
        self.assertIn("insert into ai.extraction_artifact", artifact_sql)
        self.assertIn("structured_event_candidate", artifact_sql)

    def test_run_event_intelligence_llm_extract_records_ai_and_canonical_event(self) -> None:
        executor = FakeAiEventExecutor(run_id=811)
        summary = run_event_intelligence_llm_extract(
            "0000320193-24-000123",
            config=type("Config", (), {})(),
            llm_output_json_path=str(LLM_FIXTURE),
            executor=executor,
            max_input_chars=700,
        )
        self.assertEqual(summary["run_id"], 811)
        self.assertEqual(summary["event_type"], "sec_annual_report_filed")
        self.assertEqual(summary["model_invocation_id"], 501)
        self.assertEqual(summary["artifact_id"], 601)
        self.assertIn("insert into ai.prompt_template", executor.scalar_sql[2])
        self.assertIn("insert into ai.document_chunk", executor.scalar_sql[3])
        self.assertIn("insert into ai.model_invocation", executor.scalar_sql[4])
        self.assertIn("insert into ai.extraction_artifact", executor.scalar_sql[5])
        self.assertIn("insert into event.event", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_event_intelligence_llm_extract_accepts_codex_oauth_provider_runner(self) -> None:
        executor = FakeAiEventExecutor(run_id=813)
        fixture_response = load_structured_event_provider_response(
            str(LLM_FIXTURE),
            provider=CODEX_OAUTH_PROVIDER,
            model_name="codex-cli-default",
            reasoning_effort="low",
        )

        def fake_runner(source_document, chunk, model_name, reasoning_effort):
            self.assertEqual(source_document.external_document_id, "0000320193-24-000123")
            self.assertEqual(model_name, "codex-cli-default")
            self.assertGreater(chunk.token_count, 0)
            return fixture_response

        summary = run_event_intelligence_llm_extract(
            "0000320193-24-000123",
            config=type("Config", (), {})(),
            provider=CODEX_OAUTH_PROVIDER,
            model_name="codex-cli-default",
            provider_runner=fake_runner,
            executor=executor,
            max_input_chars=700,
        )

        self.assertEqual(summary["provider"], CODEX_OAUTH_PROVIDER)
        self.assertEqual(summary["model_name"], "gpt-5.4-nano")
        self.assertEqual(summary["event_type"], "sec_annual_report_filed")

    def test_run_event_intelligence_llm_extract_marks_failed_when_event_upsert_fails(self) -> None:
        executor = FakeAiEventExecutor(run_id=812, fail_on_event_upsert=True)
        with self.assertRaisesRegex(RuntimeError, "event upsert failed"):
            run_event_intelligence_llm_extract(
                "0000320193-24-000123",
                config=type("Config", (), {})(),
                llm_output_json_path=str(LLM_FIXTURE),
                executor=executor,
                max_input_chars=700,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _source_document_record() -> SecEventSourceDocumentRecord:
    return SecEventSourceDocumentRecord(
        document_id=71,
        external_document_id="0000320193-24-000123",
        title="10-K - 10-K",
        summary="SEC 10-K filing for Apple Inc. | 10-K | file number: 001-36743",
        published_at=None,
        raw_storage_uri=(FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html").resolve().as_uri(),
        checksum="abc123",
    )
