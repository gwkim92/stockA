"""Run only deterministic prompt/provider regressions; deny real IO during tests."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
SUITES = (
    "tests.test_analysis_prompt_contract", "tests.test_agents_sdk_provider",
    "tests.test_ai_agent_registry", "tests.test_news_rss_ai_extract",
    "tests.test_news_rss_translation", "tests.test_cycle_community_ai_summary",
    "tests.test_equity_research_reporting", "tests.test_sec_ai_event_extract",
    "tests.test_news_ai_eval", "tests.test_agent_market_context",
    "tests.test_ai_ontology_validation", "tests.test_cycle_graph_context",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-sdk", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / "prompt-contract-report.json")
    args = parser.parse_args()
    try:
        sdk_version = version("openai-agents")
    except PackageNotFoundError:
        sdk_version = None
    if args.require_sdk and sdk_version is None:
        parser.error("The declared agents extra must be installed for this verification.")
    attempted_io: list[str] = []

    def deny_network(*_args, **_kwargs):
        attempted_io.append("network")
        raise RuntimeError("Real network IO is forbidden in prompt-contract tests.")

    def deny_process(*_args, **_kwargs):
        attempted_io.append("process")
        raise RuntimeError("Real process execution is forbidden in prompt-contract tests.")

    with ExitStack() as stack:
        stack.enter_context(patch("socket.socket.connect", side_effect=deny_network))
        stack.enter_context(patch("socket.create_connection", side_effect=deny_network))
        stack.enter_context(patch("subprocess.Popen", side_effect=deny_process))
        suite = unittest.defaultTestLoader.loadTestsFromNames(SUITES)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and not attempted_io and (not args.require_sdk or not result.skipped)
    report = {
        "verification": "analysis-prompt-contract-v1", "sdk_version": sdk_version,
        "suites": list(SUITES), "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "unexpected_io_attempts": len(attempted_io),
        "passed": passed, "live_model_calls": 0, "live_database_verification": False,
        "scope": "offline contract and mocked-provider regression, not model-quality evaluation",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
