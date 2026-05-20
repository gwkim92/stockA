from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from stockanalysis.operations.env_readiness import (
    ALPHA_VANTAGE_API_KEY_ENV,
    CODEX_CLI_COMMAND_ENV,
    DATABASE_URL_ENV,
    FRED_API_KEY_ENV,
    LLM_PROVIDER_ENV,
    MARKET_PRICE_BUDGET_LEDGER_PATH_ENV,
    MARKET_PRICE_PROVIDER_ENV,
    MARKET_PRICE_WATCHLIST_CSV_ENV,
    NEWS_RSS_FEED_CONFIG_ENV,
    OPENAI_API_KEY_ENV,
    PORTFOLIO_POSITIONS_CSV_ENV,
    PSQL_COMMAND_ENV,
    SEC_USER_AGENT_ENV,
    TWELVE_DATA_API_KEY_ENV,
    check_data_operations_runtime_env,
    render_data_operations_env_template,
)
from stockanalysis.operations.cadence import DATA_OPERATIONS_ARTIFACT_ROOT_ENV


class DataOperationsEnvReadinessTests(unittest.TestCase):
    def test_valid_env_passes_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root())

            self.assertEqual(report["report_name"], "data_operations_runtime_env_readiness")
            self.assertEqual(report["runtime_env_readiness"], "passed")
            self.assertIn("market_price_provider", report["validated_env_groups"])
            self.assertIn("market_price_history", report["validated_env_groups"])
            report_text = json.dumps(report)
            self.assertNotIn(env[DATABASE_URL_ENV], report_text)
            self.assertNotIn(env[FRED_API_KEY_ENV], report_text)
            self.assertNotIn(env[ALPHA_VANTAGE_API_KEY_ENV], report_text)
            self.assertNotIn(env[TWELVE_DATA_API_KEY_ENV], report_text)
            self.assertNotIn(env[OPENAI_API_KEY_ENV], report_text)
            self.assertNotIn(env[SEC_USER_AGENT_ENV], report_text)

    def test_database_can_use_legacy_psql_command_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env.pop(DATABASE_URL_ENV)
            env[PSQL_COMMAND_ENV] = sys.executable

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root())

            database_group = self._group(report, "database")
            self.assertEqual(database_group["status"], "passed")
            self.assertEqual(database_group["details"]["psql_command_argv0"], sys.executable)

    def test_missing_provider_group_fails_with_actionable_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env.pop(FRED_API_KEY_ENV)

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root(), strict=False)

            self.assertEqual(report["runtime_env_readiness"], "failed")
            fred_group = self._group(report, "fred")
            self.assertEqual(fred_group["status"], "failed")
            self.assertIn(FRED_API_KEY_ENV, fred_group["message"])

    def test_twelve_data_market_price_provider_passes_without_alpha_vantage_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env[MARKET_PRICE_PROVIDER_ENV] = "twelvedata"
            env.pop(ALPHA_VANTAGE_API_KEY_ENV)

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root())

            market_group = self._group(report, "market_price_provider")
            self.assertEqual(market_group["status"], "passed")
            self.assertEqual(market_group["details"]["provider"], "twelve_data")
            self.assertEqual(market_group["details"]["credential_env"], TWELVE_DATA_API_KEY_ENV)

    def test_market_price_provider_requires_repo_outside_watchlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env[MARKET_PRICE_WATCHLIST_CSV_ENV] = str(self._repo_root() / "README.md")

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root(), strict=False)

            market_group = self._group(report, "market_price_provider")
            self.assertEqual(market_group["status"], "failed")
            self.assertIn("outside the repository", market_group["message"])

    def test_placeholder_values_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env[ALPHA_VANTAGE_API_KEY_ENV] = "CHANGE_ME_ALPHA_VANTAGE_API_KEY"

            with self.assertRaises(ValueError) as ctx:
                check_data_operations_runtime_env(env=env, repo_root=self._repo_root())

            self.assertIn(ALPHA_VANTAGE_API_KEY_ENV, str(ctx.exception))
            self.assertIn("placeholder", str(ctx.exception))

    def test_repo_inside_sensitive_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env[PORTFOLIO_POSITIONS_CSV_ENV] = str(
                self._repo_root() / "tests" / "fixtures" / "portfolio_positions_long_term_paper.csv"
            )
            env[DATA_OPERATIONS_ARTIFACT_ROOT_ENV] = str(self._repo_root() / ".tmp-data-ops-artifacts")

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root(), strict=False)

            self.assertEqual(self._group(report, "portfolio_snapshot_source")["status"], "failed")
            self.assertEqual(self._group(report, "artifact_root")["status"], "failed")
            self.assertIn("outside the repository", " ".join(report["issues"]))

    def test_news_rss_feed_config_must_be_repo_outside(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env[NEWS_RSS_FEED_CONFIG_ENV] = str(self._repo_root() / "README.md")

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root(), strict=False)

            group = self._group(report, "news_rss_feed_config")
            self.assertEqual(group["status"], "failed")
            self.assertIn("outside the repository", group["message"])

    def test_env_file_must_be_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            report = check_data_operations_runtime_env(
                env=env,
                repo_root=self._repo_root(),
                env_file=self._repo_root() / "README.md",
                strict=False,
            )

            self.assertEqual(report["runtime_env_readiness"], "failed")
            self.assertIn("env file must be outside the repository", " ".join(report["issues"]))

    def test_template_contains_required_env_names_without_real_values(self) -> None:
        template = render_data_operations_env_template()

        self.assertIn(DATABASE_URL_ENV, template)
        self.assertIn(FRED_API_KEY_ENV, template)
        self.assertIn(MARKET_PRICE_PROVIDER_ENV, template)
        self.assertIn(TWELVE_DATA_API_KEY_ENV, template)
        self.assertIn(MARKET_PRICE_WATCHLIST_CSV_ENV, template)
        self.assertIn(MARKET_PRICE_BUDGET_LEDGER_PATH_ENV, template)
        self.assertIn(ALPHA_VANTAGE_API_KEY_ENV, template)
        self.assertIn(SEC_USER_AGENT_ENV, template)
        self.assertIn(NEWS_RSS_FEED_CONFIG_ENV, template)
        self.assertIn(PORTFOLIO_POSITIONS_CSV_ENV, template)
        self.assertIn(LLM_PROVIDER_ENV, template)
        self.assertIn(CODEX_CLI_COMMAND_ENV, template)
        self.assertIn(DATA_OPERATIONS_ARTIFACT_ROOT_ENV, template)
        self.assertIn("CHANGE_ME", template)

    def test_codex_oauth_provider_passes_without_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = self._valid_env(tmpdir)
            env[LLM_PROVIDER_ENV] = "codex_oauth"
            env[CODEX_CLI_COMMAND_ENV] = sys.executable
            env.pop(OPENAI_API_KEY_ENV)

            report = check_data_operations_runtime_env(env=env, repo_root=self._repo_root())

            group = self._group(report, "openai_or_llm_provider")
            self.assertEqual(group["status"], "passed")
            self.assertEqual(group["details"]["provider"], "codex_oauth")
            self.assertEqual(group["details"]["auth_boundary"], "codex_cli_oauth_no_token_read")

    @staticmethod
    def _repo_root() -> Path:
        return Path(__file__).resolve().parents[1]

    @staticmethod
    def _group(report: dict[str, object], group_name: str) -> dict[str, object]:
        for group in report["groups"]:
            if group["group"] == group_name:
                return group
        raise AssertionError(f"Missing group: {group_name}")

    def _valid_env(self, tmpdir: str) -> dict[str, str]:
        tmp_path = Path(tmpdir)
        positions_csv = tmp_path / "positions.csv"
        positions_csv.write_text("symbol,quantity\nAAPL,10\n", encoding="utf-8")
        market_watchlist_csv = tmp_path / "market-watchlist.csv"
        market_watchlist_csv.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")
        news_rss_config = tmp_path / "news-rss-feeds.json"
        news_rss_config.write_text(
            json.dumps(
                {
                    "version": "news-rss-feed-config-v1",
                    "feeds": [
                        {
                            "feed_name": "free-feed",
                            "feed_url": "https://example.com/free/rss",
                            "enabled": True,
                            "limit": 25,
                            "default_language": "en",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return {
            DATABASE_URL_ENV: "postgresql://runtime_user:runtime_pass@db.internal:5432/stockanalysis",
            FRED_API_KEY_ENV: "fred-runtime-token-123",
            MARKET_PRICE_PROVIDER_ENV: "alpha_vantage",
            MARKET_PRICE_WATCHLIST_CSV_ENV: str(market_watchlist_csv),
            MARKET_PRICE_BUDGET_LEDGER_PATH_ENV: str(tmp_path / "market-budget-ledger.json"),
            ALPHA_VANTAGE_API_KEY_ENV: "alpha-runtime-token-123",
            TWELVE_DATA_API_KEY_ENV: "twelve-runtime-token-123",
            SEC_USER_AGENT_ENV: "stockanalysis-test contact@operator.test",
            NEWS_RSS_FEED_CONFIG_ENV: str(news_rss_config),
            PORTFOLIO_POSITIONS_CSV_ENV: str(positions_csv),
            LLM_PROVIDER_ENV: "openai",
            OPENAI_API_KEY_ENV: "openai-runtime-key-123456",
            DATA_OPERATIONS_ARTIFACT_ROOT_ENV: str(tmp_path / "artifacts"),
        }


if __name__ == "__main__":
    unittest.main()
