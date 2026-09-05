from __future__ import annotations

import builtins
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ai_agents.agents_sdk_provider import (
    AgentsSdkProviderError,
    AgentsSdkProviderUnavailable,
    AgentsSdkStructuredRequest,
    build_agents_sdk_prompt,
    run_agents_sdk_structured_request,
)
from stockanalysis.ai_agents.runtime_policy import build_agent_runtime_policy


class AgentsSdkProviderTests(unittest.TestCase):
    def test_build_prompt_includes_agent_instructions_policy_and_schema(self) -> None:
        request = AgentsSdkStructuredRequest(
            agent_key="news_structuring_agent",
            task_name="news-rss-ai-extract",
            input_payload={"title": "Fed rate-cut odds shift", "known_themes": ["MACRO_RATES_FED"]},
            output_schema={"type": "object", "required": ["candidate"]},
        )
        policy = build_agent_runtime_policy("news_structuring_agent")

        prompt = build_agents_sdk_prompt(request=request, policy=policy)

        self.assertIn("투자 뉴스 evidence 구조화 에이전트", prompt)
        self.assertIn("거시 뉴스는 억지로 종목에 붙이지 않는다", prompt)
        self.assertIn("read_only_no_order", prompt)
        self.assertIn("MACRO_RATES_FED", prompt)
        self.assertIn('"required": ["candidate"]', prompt)

    def test_fake_runner_returns_structured_response_without_openai_call(self) -> None:
        captured: dict[str, object] = {}

        def fake_runner(request, policy, prompt):
            captured["agent_key"] = request.agent_key
            captured["policy"] = policy.as_config_json()
            captured["prompt"] = prompt
            return {
                "model_name": "fake-agent-model",
                "reasoning_effort": "low",
                "output": {"candidate": {"event_summary": "금리 기대 변화 뉴스"}},
                "usage": {
                    "input_tokens": 11,
                    "output_tokens": 7,
                    "cached_input_tokens": 3,
                    "estimated_cost_usd": "0.000120",
                    "latency_ms": 42,
                },
            }

        response = run_agents_sdk_structured_request(
            AgentsSdkStructuredRequest(
                agent_key="news_structuring_agent",
                task_name="news-rss-ai-extract",
                input_payload={"title": "Fed rate-cut odds shift"},
                output_schema={"type": "object"},
            ),
            runner=fake_runner,
        )

        self.assertEqual(captured["agent_key"], "news_structuring_agent")
        self.assertEqual(captured["policy"]["agent_order_boundary"], "read_only_no_order")
        self.assertEqual(response.provider, "agents_sdk_openai")
        self.assertEqual(response.model_name, "fake-agent-model")
        self.assertEqual(response.output["candidate"]["event_summary"], "금리 기대 변화 뉴스")
        self.assertEqual(response.input_token_count, 11)
        self.assertEqual(str(response.estimated_cost_usd), "0.000120")

    def test_string_json_output_is_accepted(self) -> None:
        response = run_agents_sdk_structured_request(
            AgentsSdkStructuredRequest(
                agent_key="news_translator_agent",
                task_name="news-rss-korean-translation",
                input_payload={"title": "Stocks rise"},
                output_schema={"type": "object"},
            ),
            runner=lambda *_args: json.dumps(
                {
                    "output": {
                        "translation": {
                            "korean_title": "주식이 상승했다",
                            "korean_summary": "원문은 주식 상승을 전했다.",
                            "translation_confidence": 0.9,
                        }
                    }
                },
                ensure_ascii=False,
            ),
        )

        self.assertEqual(response.output["translation"]["korean_title"], "주식이 상승했다")

    def test_missing_optional_agents_sdk_raises_clear_error(self) -> None:
        request = AgentsSdkStructuredRequest(
            agent_key="news_translator_agent",
            task_name="news-rss-korean-translation",
            input_payload={"title": "Stocks rise"},
            output_schema={"type": "object"},
        )

        real_import = builtins.__import__

        def missing_agents(name, *args, **kwargs):
            if name == "agents" or name.startswith("agents."):
                raise ImportError("missing")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=missing_agents):
            with self.assertRaisesRegex(AgentsSdkProviderUnavailable, "openai-agents is not installed"):
                run_agents_sdk_structured_request(request)

    def test_insufficient_quota_error_is_fallbackable(self) -> None:
        request = AgentsSdkStructuredRequest(
            agent_key="news_structuring_agent",
            task_name="news-rss-ai-extract",
            input_payload={"title": "Fed rate-cut odds shift"},
            output_schema={"type": "object"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            health_path = str(Path(tmpdir) / "provider-health.json")
            with patch.dict("os.environ", {"STOCKANALYSIS_AI_PROVIDER_HEALTH_PATH": health_path}):
                with self.assertRaises(AgentsSdkProviderError) as raised:
                    run_agents_sdk_structured_request(
                        request,
                        runner=lambda *_args: (_ for _ in ()).throw(RuntimeError("insufficient_quota: quota exceeded")),
                    )

        self.assertEqual(raised.exception.error_code, "openai_insufficient_quota")
        self.assertEqual(raised.exception.fallback_provider, "codex_oauth")
        self.assertEqual(raised.exception.local_fallback_provider, "local_rules")
        self.assertFalse(raised.exception.retryable)

    def test_cached_quota_error_skips_next_openai_call(self) -> None:
        request = AgentsSdkStructuredRequest(
            agent_key="news_translator_agent",
            task_name="news-rss-korean-translation",
            input_payload={"title": "Stocks rise"},
            output_schema={"type": "object"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            health_path = str(Path(tmpdir) / "provider-health.json")
            with patch.dict("os.environ", {"STOCKANALYSIS_AI_PROVIDER_HEALTH_PATH": health_path}):
                with self.assertRaises(AgentsSdkProviderError):
                    run_agents_sdk_structured_request(
                        request,
                        runner=lambda *_args: (_ for _ in ()).throw(RuntimeError("insufficient_quota")),
                    )
                with self.assertRaises(AgentsSdkProviderError) as raised:
                    run_agents_sdk_structured_request(request)

        self.assertEqual(raised.exception.error_code, "openai_insufficient_quota")
        self.assertEqual(raised.exception.fallback_provider, "codex_oauth")

    def test_known_zero_balance_runtime_flag_blocks_openai_call(self) -> None:
        request = AgentsSdkStructuredRequest(
            agent_key="news_translator_agent",
            task_name="news-rss-korean-translation",
            input_payload={"title": "Stocks rise"},
            output_schema={"type": "object"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            health_path = str(Path(tmpdir) / "provider-health.json")
            with patch.dict(
                "os.environ",
                {
                    "STOCKANALYSIS_OPENAI_BILLING_STATUS": "known_zero_balance",
                    "STOCKANALYSIS_AI_PROVIDER_HEALTH_PATH": health_path,
                },
            ):
                with self.assertRaises(AgentsSdkProviderError) as raised:
                    run_agents_sdk_structured_request(request)

        self.assertEqual(raised.exception.error_code, "openai_billing_unavailable")
        self.assertEqual(raised.exception.fallback_provider, "codex_oauth")
        self.assertFalse(raised.exception.retryable)

    def test_openai_disable_flag_blocks_openai_call(self) -> None:
        request = AgentsSdkStructuredRequest(
            agent_key="news_translator_agent",
            task_name="news-rss-korean-translation",
            input_payload={"title": "Stocks rise"},
            output_schema={"type": "object"},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            health_path = str(Path(tmpdir) / "provider-health.json")
            with patch.dict(
                "os.environ",
                {"STOCKANALYSIS_DISABLE_OPENAI_API": "1", "STOCKANALYSIS_AI_PROVIDER_HEALTH_PATH": health_path},
            ):
                with self.assertRaises(AgentsSdkProviderError) as raised:
                    run_agents_sdk_structured_request(request)

        self.assertEqual(raised.exception.error_code, "openai_provider_disabled")
        self.assertEqual(raised.exception.fallback_provider, "codex_oauth")


if __name__ == "__main__":
    unittest.main()
