from __future__ import annotations

import unittest
from pathlib import Path

from stockanalysis.ai_agents.registry import (
    DEFAULT_AGENT_DEFINITIONS,
    REQUIRED_AGENT_KEYS,
    build_agent_registry_summary,
    get_agent_definition,
)
from stockanalysis.operations.ai_agent_registry import build_ai_agent_registry_report


REPO_ROOT = Path(__file__).resolve().parents[1]


class AiAgentRegistryTests(unittest.TestCase):
    def test_catalog_contains_required_agents_once(self) -> None:
        keys = [agent.agent_key for agent in DEFAULT_AGENT_DEFINITIONS]

        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(tuple(keys), REQUIRED_AGENT_KEYS)

    def test_all_agents_keep_order_and_canonical_write_boundaries(self) -> None:
        for agent in DEFAULT_AGENT_DEFINITIONS:
            with self.subTest(agent=agent.agent_key):
                self.assertFalse(agent.can_trigger_order)
                self.assertFalse(agent.can_write_canonical)
                self.assertTrue(agent.requires_approval_for_side_effects)
                self.assertIn("read_only_no_order", agent.prompt.instructions)
                self.assertIn("deterministic validators", agent.prompt.instructions)

    def test_specialized_prompts_are_professional_and_korean_first(self) -> None:
        news = get_agent_definition("news_structuring_agent")
        equity = get_agent_definition("equity_research_agent")
        portfolio = get_agent_definition("portfolio_risk_agent")

        self.assertIn("macro_regime_impacts", news.prompt.instructions)
        self.assertIn("direct_instrument_impacts", news.prompt.instructions)
        self.assertIn("거시 뉴스는 억지로 종목에 붙이지 않는다", news.prompt.instructions)
        self.assertIn("사업 스토리와 숫자", equity.prompt.instructions)
        self.assertIn("source gap", equity.prompt.instructions)
        self.assertIn("benchmark drift", portfolio.prompt.instructions)
        self.assertIn("사람이 읽는 모든 설명은 한국어", news.prompt.instructions)

    def test_model_policies_are_admin_configurable_with_fallbacks(self) -> None:
        summary = build_agent_registry_summary()

        self.assertEqual(summary["model_control_surface"], "admin_only")
        self.assertEqual(summary["default_primary_provider"], "agents_sdk_openai")
        self.assertEqual(summary["default_fallback_provider"], "codex_oauth")
        self.assertEqual(summary["default_local_fallback_provider"], "local_rules")
        for agent in DEFAULT_AGENT_DEFINITIONS:
            with self.subTest(agent=agent.agent_key):
                self.assertEqual(agent.model_policy.primary_provider, "agents_sdk_openai")
                self.assertEqual(agent.model_policy.primary_model, "gpt-5.5")
                self.assertEqual(agent.model_policy.fallback_provider, "codex_oauth")
                self.assertGreater(agent.model_policy.max_requests_per_run, 0)

    def test_registry_report_hides_prompts_by_default(self) -> None:
        report = build_ai_agent_registry_report()
        prompt_report = build_ai_agent_registry_report(include_prompts=True)

        self.assertEqual(report["status"], "loaded")
        self.assertEqual(report["agent_count"], len(REQUIRED_AGENT_KEYS))
        self.assertNotIn("instructions", report["agents"][0])
        self.assertIn("instructions", prompt_report["agents"][0])
        self.assertEqual(report["agents"][0]["safety_boundary"]["order_boundary"], "read_only_no_order")

    def test_db_migration_and_seed_cover_catalog(self) -> None:
        migration = (REPO_ROOT / "db/migrations/0032_ai_agent_registry.sql").read_text(encoding="utf-8")
        seed = (REPO_ROOT / "db/seeds/0007_ai_agent_registry_seed.sql").read_text(encoding="utf-8")
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        for table_name in (
            "ai.agent_definition",
            "ai.agent_prompt_version",
            "ai.agent_model_policy",
            "ai.agent_tool_permission",
            "ai.agent_run",
        ):
            self.assertIn(table_name, migration)
        self.assertIn("check (can_trigger_order = false)", migration)
        for agent in DEFAULT_AGENT_DEFINITIONS:
            with self.subTest(agent=agent.agent_key):
                self.assertIn(agent.agent_key, seed)
                self.assertIn(agent.prompt.prompt_version, seed)
                self.assertIn(agent.prompt.prompt_cache_key, seed)
        self.assertIn("openai-agents>=0.17.5,<0.18", pyproject)


if __name__ == "__main__":
    unittest.main()
