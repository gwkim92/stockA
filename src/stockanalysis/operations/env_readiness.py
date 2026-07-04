from __future__ import annotations

import os
import shlex
import shutil
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from stockanalysis.operations.cadence import (
    DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
    list_data_operation_cadences,
)
from stockanalysis.operations.news_rss_feed_runner import (
    NEWS_RSS_FEED_CONFIG_ENV,
    load_news_rss_feed_config,
)


DATABASE_URL_ENV = "STOCKANALYSIS_DATABASE_URL"
PSQL_COMMAND_ENV = "STOCKANALYSIS_PSQL_COMMAND"
FRED_API_KEY_ENV = "STOCKANALYSIS_FRED_API_KEY"
ALPHA_VANTAGE_API_KEY_ENV = "STOCKANALYSIS_ALPHA_VANTAGE_API_KEY"
TWELVE_DATA_API_KEY_ENV = "STOCKANALYSIS_TWELVE_DATA_API_KEY"
MARKET_PRICE_PROVIDER_ENV = "STOCKANALYSIS_MARKET_PRICE_PROVIDER"
MARKET_PRICE_WATCHLIST_CSV_ENV = "STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV"
MARKET_PRICE_BUDGET_LEDGER_PATH_ENV = "STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH"
MARKET_PRICE_DAILY_BUDGET_ENV = "STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET"
MARKET_PRICE_MAX_REQUESTS_PER_RUN_ENV = "STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN"
MARKET_PRICE_THROTTLE_SECONDS_ENV = "STOCKANALYSIS_MARKET_PRICE_THROTTLE_SECONDS"
MARKET_PRICE_OUTPUTSIZE_ENV = "STOCKANALYSIS_MARKET_PRICE_OUTPUTSIZE"
SEC_USER_AGENT_ENV = "STOCKANALYSIS_SEC_USER_AGENT"
PORTFOLIO_POSITIONS_CSV_ENV = "STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV"
LLM_PROVIDER_ENV = "STOCKANALYSIS_LLM_PROVIDER"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
CODEX_CLI_COMMAND_ENV = "STOCKANALYSIS_CODEX_CLI_COMMAND"
TOSSINVEST_CLIENT_ID_ENV = "STOCKANALYSIS_TOSSINVEST_CLIENT_ID"
TOSSINVEST_CLIENT_SECRET_ENV = "STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET"
TOSSINVEST_ACCOUNT_SEQ_ENV = "STOCKANALYSIS_TOSSINVEST_ACCOUNT_SEQ"

_LLM_PROVIDER_KEY_ENVS = (
    OPENAI_API_KEY_ENV,
    "STOCKANALYSIS_LLM_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "AZURE_OPENAI_API_KEY",
)
_PLACEHOLDER_TOKENS = (
    "CHANGE_ME",
    "USER:PASSWORD@HOST",
    "YYYY-MM-DD",
    "/absolute/path",
    "example.com",
    "example.invalid",
    "replace-me",
    "replace-with",
    "TODO",
)
_SUPPORTED_ENV_GROUPS = (
    "database",
    "fred",
    "alpha_vantage",
    "market_price_provider",
    "sec_identity",
    "portfolio_snapshot_source",
    "news_rss_feed_config",
    "openai_or_llm_provider",
    "market_price_history",
    "artifact_root",
    "tossinvest",
)


def render_data_operations_env_template() -> str:
    return "\n".join(
        (
            "# Stockanalysis data operations env.",
            "# This file is sourced as shell by data operations checker/scheduler wrappers.",
            "# Keep it outside the repository and do not commit credentials.",
            "",
            "# Database boundary. Prefer STOCKANALYSIS_DATABASE_URL for Python runtimes.",
            'STOCKANALYSIS_DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/stockanalysis"',
            "# Optional legacy psql shell-out boundary for existing ingest commands.",
            '# STOCKANALYSIS_PSQL_COMMAND="psql postgresql://USER:PASSWORD@HOST:5432/stockanalysis"',
            "",
            "# External data providers.",
            'STOCKANALYSIS_FRED_API_KEY="CHANGE_ME_FRED_API_KEY"',
            "# Market price provider. Use Twelve Data for the no-cost broad-market MVP path.",
            'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
            'STOCKANALYSIS_TWELVE_DATA_API_KEY="CHANGE_ME_TWELVE_DATA_API_KEY"',
            '# STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="CHANGE_ME_ALPHA_VANTAGE_API_KEY"',
            'STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="/absolute/path/to/market-price-watchlist.csv"',
            'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="/absolute/path/to/market-price-budget-ledger.json"',
            'STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET="800"',
            'STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN="50"',
            'STOCKANALYSIS_MARKET_PRICE_THROTTLE_SECONDS="8"',
            'STOCKANALYSIS_MARKET_PRICE_OUTPUTSIZE="100"',
            'STOCKANALYSIS_SEC_USER_AGENT="stockanalysis/0.1 contact@example.com"',
            'STOCKANALYSIS_NEWS_RSS_FEED_CONFIG_JSON="/absolute/path/to/news-rss-feeds.json"',
            "",
            "# Portfolio snapshot source. Keep position files outside the repository.",
            'STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="/absolute/path/to/positions.csv"',
            "",
            "# AI provider boundary for event/thesis interpretation. Fixture mode is not runtime-ready.",
            'STOCKANALYSIS_LLM_PROVIDER="openai"',
            'OPENAI_API_KEY="CHANGE_ME_OPENAI_API_KEY"',
            '# No-cost Codex OAuth boundary. Uses `codex exec`; does not read or copy Codex auth tokens.',
            '# STOCKANALYSIS_LLM_PROVIDER="codex_oauth"',
            '# STOCKANALYSIS_CODEX_CLI_COMMAND="codex"',
            "# Alternative non-OpenAI providers can use STOCKANALYSIS_LLM_API_KEY or provider-specific env keys.",
            '# STOCKANALYSIS_LLM_API_KEY="CHANGE_ME_PROVIDER_API_KEY"',
            "",
            "# Data operations artifact root. Keep stdout/stderr/metadata outside the repository.",
            'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="/absolute/path/to/data-operations-artifacts"',
            "",
            "# TossInvest broker reality data. Required for Toss profiles; account seq is optional.",
            'STOCKANALYSIS_TOSSINVEST_CLIENT_ID="CHANGE_ME_TOSSINVEST_CLIENT_ID"',
            'STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET="CHANGE_ME_TOSSINVEST_CLIENT_SECRET"',
            '# STOCKANALYSIS_TOSSINVEST_ACCOUNT_SEQ="OPTIONAL_ACCOUNT_SEQ"',
            "",
        )
    )


def check_data_operations_runtime_env(
    *,
    env: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
    env_file: str | Path | None = None,
    strict: bool = True,
) -> dict[str, object]:
    env_mapping = env if env is not None else os.environ
    root = Path(repo_root or Path.cwd()).resolve()

    env_file_path = Path(env_file).resolve() if env_file is not None else None
    groups: list[dict[str, object]] = []
    issues: list[str] = []

    if env_file_path is not None:
        issue = _validate_repo_outside_existing_file(env_file_path, root, label="data operations env file")
        if issue:
            issues.append(issue)

    database_group, database_ready = _validate_database(env_mapping)
    groups.append(database_group)
    _append_group_issue(groups[-1], issues)

    for validator in (
        _validate_fred,
        lambda mapping: _validate_market_price_provider(mapping, repo_root=root),
        _validate_sec_identity,
        lambda mapping: _validate_news_rss_feed_config(mapping, repo_root=root),
        lambda mapping: _validate_portfolio_positions(mapping, repo_root=root),
        _validate_llm_provider,
        lambda mapping: _validate_market_price_history(mapping, database_ready=database_ready),
        lambda mapping: _validate_artifact_root(mapping, repo_root=root),
        _validate_tossinvest,
    ):
        group = validator(env_mapping)
        groups.append(group)
        _append_group_issue(group, issues)

    cadence_groups = sorted(
        {group for job in list_data_operation_cadences() for group in job.required_env_groups}
    )
    unknown_cadence_groups = sorted(set(cadence_groups) - set(_SUPPORTED_ENV_GROUPS))
    if unknown_cadence_groups:
        issues.append(f"Unsupported cadence env groups: {', '.join(unknown_cadence_groups)}")

    report = {
        "report_name": "data_operations_runtime_env_readiness",
        "runtime_env_readiness": "failed" if issues else "passed",
        "env_file": str(env_file_path) if env_file_path is not None else "",
        "cadence_job_count": len(list_data_operation_cadences()),
        "cadence_required_env_groups": cadence_groups,
        "validated_env_groups": [group["group"] for group in groups],
        "groups": groups,
        "secrets_policy": "values_redacted_env_names_only",
        "activation_boundary": "readiness_check_only_no_scheduler_activation",
        "issues": issues,
    }
    if issues and strict:
        raise ValueError("Data operations runtime env readiness failed: " + "; ".join(issues))
    return report


def _validate_database(env: Mapping[str, str]) -> tuple[dict[str, object], bool]:
    database_url = _env_value(env, DATABASE_URL_ENV)
    psql_command = _env_value(env, PSQL_COMMAND_ENV)
    configured = [name for name, value in ((DATABASE_URL_ENV, database_url), (PSQL_COMMAND_ENV, psql_command)) if value]

    if not configured:
        return (
            _failed_group(
                "database",
                required_env=[DATABASE_URL_ENV, PSQL_COMMAND_ENV],
                configured_env=[],
                message=f"Configure either {DATABASE_URL_ENV} or {PSQL_COMMAND_ENV}.",
            ),
            False,
        )

    messages: list[str] = []
    details: dict[str, object] = {}
    if database_url:
        url_issue = _validate_database_url(database_url)
        if url_issue:
            messages.append(url_issue)
        else:
            details["database_boundary"] = "database_url"
    if psql_command:
        command_issue, argv0 = _validate_psql_command(psql_command)
        if command_issue:
            messages.append(command_issue)
        else:
            details["psql_command_argv0"] = argv0
            details.setdefault("database_boundary", "psql_command")

    if messages:
        return (
            _failed_group(
                "database",
                required_env=[DATABASE_URL_ENV, PSQL_COMMAND_ENV],
                configured_env=configured,
                message="; ".join(messages),
            ),
            False,
        )
    return (
        _passed_group(
            "database",
            required_env=[DATABASE_URL_ENV, PSQL_COMMAND_ENV],
            configured_env=configured,
            details=details,
        ),
        True,
    )


def _validate_fred(env: Mapping[str, str]) -> dict[str, object]:
    return _validate_secret_env(
        env,
        group="fred",
        env_name=FRED_API_KEY_ENV,
        min_length=8,
    )


def _validate_market_price_provider(env: Mapping[str, str], *, repo_root: Path) -> dict[str, object]:
    raw_provider = _env_value(env, MARKET_PRICE_PROVIDER_ENV)
    if not raw_provider:
        return _failed_group(
            "market_price_provider",
            required_env=[MARKET_PRICE_PROVIDER_ENV],
            configured_env=[],
            message=f"Missing required environment variable: {MARKET_PRICE_PROVIDER_ENV}.",
        )
    provider = _normalize_market_price_provider(raw_provider)
    if not provider:
        return _failed_group(
            "market_price_provider",
            required_env=[MARKET_PRICE_PROVIDER_ENV],
            configured_env=[MARKET_PRICE_PROVIDER_ENV],
            message=f"Unsupported market price provider: {raw_provider}.",
        )

    key_env = TWELVE_DATA_API_KEY_ENV if provider == "twelve_data" else ALPHA_VANTAGE_API_KEY_ENV
    required_env = [
        MARKET_PRICE_PROVIDER_ENV,
        key_env,
        MARKET_PRICE_WATCHLIST_CSV_ENV,
        MARKET_PRICE_BUDGET_LEDGER_PATH_ENV,
    ]
    configured_env = [name for name in required_env if _env_value(env, name)]

    key_value = _env_value(env, key_env)
    if not key_value:
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=f"Missing required environment variable: {key_env}.",
        )
    key_issue = _placeholder_issue(key_env, key_value)
    if key_issue:
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=key_issue,
        )
    if len(key_value) < 4:
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=f"{key_env} must not be a short placeholder-like value.",
        )

    if not _env_value(env, MARKET_PRICE_WATCHLIST_CSV_ENV):
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=f"Missing required environment variable: {MARKET_PRICE_WATCHLIST_CSV_ENV}.",
        )
    watchlist_issue = _validate_repo_outside_existing_file(
        Path(_env_value(env, MARKET_PRICE_WATCHLIST_CSV_ENV)),
        repo_root,
        label="market price watchlist CSV",
    )
    if watchlist_issue:
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=watchlist_issue,
        )

    if not _env_value(env, MARKET_PRICE_BUDGET_LEDGER_PATH_ENV):
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=f"Missing required environment variable: {MARKET_PRICE_BUDGET_LEDGER_PATH_ENV}.",
        )
    ledger_issue = _validate_repo_outside_output_file(
        Path(_env_value(env, MARKET_PRICE_BUDGET_LEDGER_PATH_ENV)),
        repo_root,
        label="market price budget ledger",
    )
    if ledger_issue:
        return _failed_group(
            "market_price_provider",
            required_env=required_env,
            configured_env=configured_env,
            message=ledger_issue,
        )

    for int_env in (MARKET_PRICE_DAILY_BUDGET_ENV, MARKET_PRICE_MAX_REQUESTS_PER_RUN_ENV):
        value = _env_value(env, int_env)
        if value and (not value.isdigit() or int(value) < 0):
            return _failed_group(
                "market_price_provider",
                required_env=required_env,
                configured_env=configured_env,
                message=f"{int_env} must be a non-negative integer.",
            )
    throttle = _env_value(env, MARKET_PRICE_THROTTLE_SECONDS_ENV)
    if throttle:
        try:
            if float(throttle) < 0:
                raise ValueError
        except ValueError:
            return _failed_group(
                "market_price_provider",
                required_env=required_env,
                configured_env=configured_env,
                message=f"{MARKET_PRICE_THROTTLE_SECONDS_ENV} must be a non-negative number.",
            )

    optional_configured = [
        name
        for name in (
            MARKET_PRICE_DAILY_BUDGET_ENV,
            MARKET_PRICE_MAX_REQUESTS_PER_RUN_ENV,
            MARKET_PRICE_THROTTLE_SECONDS_ENV,
            MARKET_PRICE_OUTPUTSIZE_ENV,
        )
        if _env_value(env, name)
    ]
    return _passed_group(
        "market_price_provider",
        required_env=required_env,
        configured_env=[*configured_env, *optional_configured],
        details={
            "provider": provider,
            "credential_env": key_env,
            "watchlist_configured": True,
            "budget_ledger_configured": True,
        },
    )


def _validate_sec_identity(env: Mapping[str, str]) -> dict[str, object]:
    value = _env_value(env, SEC_USER_AGENT_ENV)
    if not value:
        return _failed_group(
            "sec_identity",
            required_env=[SEC_USER_AGENT_ENV],
            configured_env=[],
            message=f"Missing required environment variable: {SEC_USER_AGENT_ENV}.",
        )
    issue = _placeholder_issue(SEC_USER_AGENT_ENV, value)
    if issue:
        return _failed_group(
            "sec_identity",
            required_env=[SEC_USER_AGENT_ENV],
            configured_env=[SEC_USER_AGENT_ENV],
            message=issue,
        )
    if len(value) < 12 or not any(marker in value for marker in ("@", "http://", "https://")):
        return _failed_group(
            "sec_identity",
            required_env=[SEC_USER_AGENT_ENV],
            configured_env=[SEC_USER_AGENT_ENV],
            message=f"{SEC_USER_AGENT_ENV} must include a descriptive app name and contact marker.",
        )
    return _passed_group(
        "sec_identity",
        required_env=[SEC_USER_AGENT_ENV],
        configured_env=[SEC_USER_AGENT_ENV],
        details={"contact_marker_configured": True},
    )


def _validate_portfolio_positions(env: Mapping[str, str], *, repo_root: Path) -> dict[str, object]:
    value = _env_value(env, PORTFOLIO_POSITIONS_CSV_ENV)
    if not value:
        return _failed_group(
            "portfolio_snapshot_source",
            required_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            configured_env=[],
            message=f"Missing required environment variable: {PORTFOLIO_POSITIONS_CSV_ENV}.",
        )
    issue = _placeholder_issue(PORTFOLIO_POSITIONS_CSV_ENV, value)
    if issue:
        return _failed_group(
            "portfolio_snapshot_source",
            required_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            configured_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            message=issue,
        )
    path = Path(value)
    if not path.is_absolute():
        return _failed_group(
            "portfolio_snapshot_source",
            required_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            configured_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            message=f"{PORTFOLIO_POSITIONS_CSV_ENV} must be an absolute path.",
        )
    resolved_path = path.resolve()
    if _is_relative_to(resolved_path, repo_root):
        return _failed_group(
            "portfolio_snapshot_source",
            required_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            configured_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            message=f"{PORTFOLIO_POSITIONS_CSV_ENV} must point outside the repository.",
        )
    if not resolved_path.is_file():
        return _failed_group(
            "portfolio_snapshot_source",
            required_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            configured_env=[PORTFOLIO_POSITIONS_CSV_ENV],
            message=f"{PORTFOLIO_POSITIONS_CSV_ENV} must point to an existing CSV file.",
        )
    return _passed_group(
        "portfolio_snapshot_source",
        required_env=[PORTFOLIO_POSITIONS_CSV_ENV],
        configured_env=[PORTFOLIO_POSITIONS_CSV_ENV],
        details={"positions_csv_configured": True},
    )


def _validate_news_rss_feed_config(env: Mapping[str, str], *, repo_root: Path) -> dict[str, object]:
    value = _env_value(env, NEWS_RSS_FEED_CONFIG_ENV)
    if not value:
        return _failed_group(
            "news_rss_feed_config",
            required_env=[NEWS_RSS_FEED_CONFIG_ENV],
            configured_env=[],
            message=f"Missing required environment variable: {NEWS_RSS_FEED_CONFIG_ENV}.",
        )
    issue = _placeholder_issue(NEWS_RSS_FEED_CONFIG_ENV, value)
    if issue:
        return _failed_group(
            "news_rss_feed_config",
            required_env=[NEWS_RSS_FEED_CONFIG_ENV],
            configured_env=[NEWS_RSS_FEED_CONFIG_ENV],
            message=issue,
        )
    path = Path(value)
    if not path.is_absolute():
        return _failed_group(
            "news_rss_feed_config",
            required_env=[NEWS_RSS_FEED_CONFIG_ENV],
            configured_env=[NEWS_RSS_FEED_CONFIG_ENV],
            message=f"{NEWS_RSS_FEED_CONFIG_ENV} must be an absolute path.",
        )
    path_issue = _validate_repo_outside_existing_file(path.resolve(), repo_root, label="news RSS feed config")
    if path_issue:
        return _failed_group(
            "news_rss_feed_config",
            required_env=[NEWS_RSS_FEED_CONFIG_ENV],
            configured_env=[NEWS_RSS_FEED_CONFIG_ENV],
            message=path_issue,
        )
    try:
        feeds = load_news_rss_feed_config(path, repo_root=repo_root)
    except (json.JSONDecodeError, ValueError, FileNotFoundError) as exc:
        return _failed_group(
            "news_rss_feed_config",
            required_env=[NEWS_RSS_FEED_CONFIG_ENV],
            configured_env=[NEWS_RSS_FEED_CONFIG_ENV],
            message=f"Invalid news RSS feed config: {exc}",
        )
    enabled_feed_count = sum(1 for feed in feeds if feed.enabled)
    if enabled_feed_count <= 0:
        return _failed_group(
            "news_rss_feed_config",
            required_env=[NEWS_RSS_FEED_CONFIG_ENV],
            configured_env=[NEWS_RSS_FEED_CONFIG_ENV],
            message="news RSS feed config must contain at least one enabled feed.",
        )
    return _passed_group(
        "news_rss_feed_config",
        required_env=[NEWS_RSS_FEED_CONFIG_ENV],
        configured_env=[NEWS_RSS_FEED_CONFIG_ENV],
        details={
            "feed_count": len(feeds),
            "enabled_feed_count": enabled_feed_count,
            "free_provider_policy": "rss_atom_no_api_key",
            "redaction_policy": "full_feed_urls_omitted",
        },
    )


def _validate_llm_provider(env: Mapping[str, str]) -> dict[str, object]:
    provider = _env_value(env, LLM_PROVIDER_ENV).lower()
    if not provider:
        return _failed_group(
            "openai_or_llm_provider",
            required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
            configured_env=[],
            message=f"Missing required environment variable: {LLM_PROVIDER_ENV}.",
        )
    issue = _placeholder_issue(LLM_PROVIDER_ENV, provider)
    if issue:
        return _failed_group(
            "openai_or_llm_provider",
            required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
            configured_env=[LLM_PROVIDER_ENV],
            message=issue,
        )
    if provider in {"fixture", "mock", "none", "disabled"}:
        return _failed_group(
            "openai_or_llm_provider",
            required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
            configured_env=[LLM_PROVIDER_ENV],
            message=f"{LLM_PROVIDER_ENV} must not be {provider!r} for runtime readiness.",
        )
    if provider == "codex_oauth":
        command_value = _env_value(env, CODEX_CLI_COMMAND_ENV) or "codex"
        command_issue, argv0 = _validate_shell_command(
            command_value,
            env_name=CODEX_CLI_COMMAND_ENV,
        )
        if command_issue:
            return _failed_group(
                "openai_or_llm_provider",
                required_env=[LLM_PROVIDER_ENV, CODEX_CLI_COMMAND_ENV],
                configured_env=[name for name in (LLM_PROVIDER_ENV, CODEX_CLI_COMMAND_ENV) if _env_value(env, name)],
                message=command_issue,
            )
        return _passed_group(
            "openai_or_llm_provider",
            required_env=[LLM_PROVIDER_ENV, CODEX_CLI_COMMAND_ENV],
            configured_env=[name for name in (LLM_PROVIDER_ENV, CODEX_CLI_COMMAND_ENV) if _env_value(env, name)],
            details={
                "provider": provider,
                "auth_boundary": "codex_cli_oauth_no_token_read",
                "codex_command_argv0": argv0,
            },
        )

    key_envs = [name for name in _LLM_PROVIDER_KEY_ENVS if _env_value(env, name)]
    if provider == "openai" and OPENAI_API_KEY_ENV not in key_envs:
        return _failed_group(
            "openai_or_llm_provider",
            required_env=[LLM_PROVIDER_ENV, OPENAI_API_KEY_ENV],
            configured_env=[LLM_PROVIDER_ENV, *key_envs],
            message=f"{OPENAI_API_KEY_ENV} is required when {LLM_PROVIDER_ENV}=openai.",
        )
    if not key_envs:
        return _failed_group(
            "openai_or_llm_provider",
            required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
            configured_env=[LLM_PROVIDER_ENV],
            message="Configure one provider API key env for the selected LLM provider.",
        )

    for key_env in key_envs:
        value = _env_value(env, key_env)
        issue = _placeholder_issue(key_env, value)
        if issue:
            return _failed_group(
                "openai_or_llm_provider",
                required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
                configured_env=[LLM_PROVIDER_ENV, *key_envs],
                message=issue,
            )
        if len(value) < 8:
            return _failed_group(
                "openai_or_llm_provider",
                required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
                configured_env=[LLM_PROVIDER_ENV, *key_envs],
                message=f"{key_env} must not be a short placeholder-like value.",
            )

    return _passed_group(
        "openai_or_llm_provider",
        required_env=[LLM_PROVIDER_ENV, *_LLM_PROVIDER_KEY_ENVS],
        configured_env=[LLM_PROVIDER_ENV, *key_envs],
        details={"provider": provider, "provider_key_configured": True},
    )


def _validate_market_price_history(env: Mapping[str, str], *, database_ready: bool) -> dict[str, object]:
    if not database_ready:
        return _failed_group(
            "market_price_history",
            required_env=[DATABASE_URL_ENV, PSQL_COMMAND_ENV],
            configured_env=[name for name in (DATABASE_URL_ENV, PSQL_COMMAND_ENV) if _env_value(env, name)],
            message="market_price_history readiness depends on a configured database boundary.",
        )
    return _passed_group(
        "market_price_history",
        required_env=[DATABASE_URL_ENV, PSQL_COMMAND_ENV],
        configured_env=[name for name in (DATABASE_URL_ENV, PSQL_COMMAND_ENV) if _env_value(env, name)],
        details={"covered_by_database_state": True},
    )


def _validate_artifact_root(env: Mapping[str, str], *, repo_root: Path) -> dict[str, object]:
    value = _env_value(env, DATA_OPERATIONS_ARTIFACT_ROOT_ENV)
    if not value:
        return _failed_group(
            "artifact_root",
            required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            configured_env=[],
            message=f"Missing required environment variable: {DATA_OPERATIONS_ARTIFACT_ROOT_ENV}.",
        )
    issue = _placeholder_issue(DATA_OPERATIONS_ARTIFACT_ROOT_ENV, value)
    if issue:
        return _failed_group(
            "artifact_root",
            required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            configured_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            message=issue,
        )
    path = Path(value)
    if not path.is_absolute():
        return _failed_group(
            "artifact_root",
            required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            configured_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            message=f"{DATA_OPERATIONS_ARTIFACT_ROOT_ENV} must be an absolute path.",
        )
    resolved_path = path.resolve()
    if _is_relative_to(resolved_path, repo_root):
        return _failed_group(
            "artifact_root",
            required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            configured_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            message=f"{DATA_OPERATIONS_ARTIFACT_ROOT_ENV} must point outside the repository.",
        )
    try:
        resolved_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return _failed_group(
            "artifact_root",
            required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            configured_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            message=f"{DATA_OPERATIONS_ARTIFACT_ROOT_ENV} cannot be created: {exc}.",
        )
    if not resolved_path.is_dir() or not os.access(resolved_path, os.W_OK):
        return _failed_group(
            "artifact_root",
            required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            configured_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
            message=f"{DATA_OPERATIONS_ARTIFACT_ROOT_ENV} must point to a writable directory.",
        )
    return _passed_group(
        "artifact_root",
        required_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
        configured_env=[DATA_OPERATIONS_ARTIFACT_ROOT_ENV],
        details={"artifact_root_configured": True},
    )


def _validate_tossinvest(env: Mapping[str, str]) -> dict[str, object]:
    client_id = _env_value(env, TOSSINVEST_CLIENT_ID_ENV)
    client_secret = _env_value(env, TOSSINVEST_CLIENT_SECRET_ENV)
    account_seq = _env_value(env, TOSSINVEST_ACCOUNT_SEQ_ENV)
    configured = [
        name
        for name, value in (
            (TOSSINVEST_CLIENT_ID_ENV, client_id),
            (TOSSINVEST_CLIENT_SECRET_ENV, client_secret),
            (TOSSINVEST_ACCOUNT_SEQ_ENV, account_seq),
        )
        if value
    ]
    required = [TOSSINVEST_CLIENT_ID_ENV, TOSSINVEST_CLIENT_SECRET_ENV]
    missing = [
        name
        for name, value in (
            (TOSSINVEST_CLIENT_ID_ENV, client_id),
            (TOSSINVEST_CLIENT_SECRET_ENV, client_secret),
        )
        if not value
    ]
    if missing:
        return _failed_group(
            "tossinvest",
            required_env=required,
            configured_env=configured,
            message=f"Missing required TossInvest environment variables: {', '.join(missing)}.",
        )

    for env_name, value in (
        (TOSSINVEST_CLIENT_ID_ENV, client_id),
        (TOSSINVEST_CLIENT_SECRET_ENV, client_secret),
    ):
        issue = _placeholder_issue(env_name, value)
        if issue:
            return _failed_group(
                "tossinvest",
                required_env=required,
                configured_env=configured,
                message=issue,
            )
        if len(value) < 8:
            return _failed_group(
                "tossinvest",
                required_env=required,
                configured_env=configured,
                message=f"{env_name} must not be a short placeholder-like value.",
            )

    return _passed_group(
        "tossinvest",
        required_env=required,
        configured_env=configured,
        details={
            "credential_configured": True,
            "selected_account_seq_configured": bool(account_seq),
            "account_seq_policy": "optional_select_first_account_if_absent",
        },
    )


def _validate_secret_env(
    env: Mapping[str, str],
    *,
    group: str,
    env_name: str,
    min_length: int,
) -> dict[str, object]:
    value = _env_value(env, env_name)
    if not value:
        return _failed_group(
            group,
            required_env=[env_name],
            configured_env=[],
            message=f"Missing required environment variable: {env_name}.",
        )
    issue = _placeholder_issue(env_name, value)
    if issue:
        return _failed_group(
            group,
            required_env=[env_name],
            configured_env=[env_name],
            message=issue,
        )
    if len(value) < min_length:
        return _failed_group(
            group,
            required_env=[env_name],
            configured_env=[env_name],
            message=f"{env_name} must not be a short placeholder-like value.",
        )
    return _passed_group(
        group,
        required_env=[env_name],
        configured_env=[env_name],
        details={"credential_configured": True},
    )


def _validate_database_url(value: str) -> str:
    issue = _placeholder_issue(DATABASE_URL_ENV, value)
    if issue:
        return issue
    parsed = urlparse(value)
    if parsed.scheme not in {"postgresql", "postgres"}:
        return f"{DATABASE_URL_ENV} must use postgres/postgresql scheme."
    if not parsed.hostname or not parsed.path or parsed.path == "/":
        return f"{DATABASE_URL_ENV} must include host and database name."
    if parsed.username is None:
        return f"{DATABASE_URL_ENV} must include a database user."
    return ""


def _validate_psql_command(value: str) -> tuple[str, str]:
    issue = _placeholder_issue(PSQL_COMMAND_ENV, value)
    if issue:
        return issue, ""
    return _validate_shell_command(value, env_name=PSQL_COMMAND_ENV)


def _validate_shell_command(value: str, *, env_name: str) -> tuple[str, str]:
    try:
        argv = shlex.split(value)
    except ValueError as exc:
        return f"Invalid {env_name}: {exc}.", ""
    if not argv:
        return f"{env_name} is empty.", ""
    argv0 = argv[0]
    if shutil.which(argv0) is None:
        return f"Missing command for {env_name}: {argv0}.", argv0
    return "", argv0


def _validate_repo_outside_existing_file(path: Path, repo_root: Path, *, label: str) -> str:
    if not path.is_file():
        return f"{label} does not exist: {path}"
    if _is_relative_to(path, repo_root):
        return f"{label} must be outside the repository: {path}"
    return ""


def _validate_repo_outside_output_file(path: Path, repo_root: Path, *, label: str) -> str:
    if not path.is_absolute():
        return f"{label} must be an absolute path."
    resolved_path = path.resolve()
    if _is_relative_to(resolved_path, repo_root):
        return f"{label} must be outside the repository: {resolved_path}"
    if resolved_path.exists() and not resolved_path.is_file():
        return f"{label} must be a file path: {resolved_path}"
    parent = resolved_path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return f"{label} parent cannot be created: {exc}."
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        return f"{label} parent must be a writable directory: {parent}"
    return ""


def _normalize_market_price_provider(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "alpha_vantage": "alpha_vantage",
        "alphavantage": "alpha_vantage",
        "av": "alpha_vantage",
        "twelve_data": "twelve_data",
        "twelvedata": "twelve_data",
        "12data": "twelve_data",
    }
    return aliases.get(normalized, "")


def _passed_group(
    group: str,
    *,
    required_env: list[str],
    configured_env: list[str],
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "group": group,
        "status": "passed",
        "required_env": required_env,
        "configured_env": configured_env,
        "details": details or {},
    }


def _failed_group(
    group: str,
    *,
    required_env: list[str],
    configured_env: list[str],
    message: str,
) -> dict[str, object]:
    return {
        "group": group,
        "status": "failed",
        "required_env": required_env,
        "configured_env": configured_env,
        "details": {},
        "message": message,
    }


def _append_group_issue(group: dict[str, object], issues: list[str]) -> None:
    if group.get("status") == "failed":
        issues.append(str(group.get("message", f"{group['group']} failed.")))


def _env_value(env: Mapping[str, str], name: str) -> str:
    return str(env.get(name, "")).strip()


def _placeholder_issue(name: str, value: str) -> str:
    upper_value = value.upper()
    for token in _PLACEHOLDER_TOKENS:
        if token.upper() in upper_value:
            return f"{name} still contains a placeholder value."
    return ""


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True
