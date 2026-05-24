from __future__ import annotations

import argparse
import os
import sys
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterator, Mapping, Sequence, TextIO

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.news.ai_extract import CODEX_OAUTH_PROVIDER, run_news_rss_ai_extract
from stockanalysis.ingest.news.cluster_evidence import run_news_rss_cluster_evidence
from stockanalysis.ingest.news.enrichment import (
    run_news_missing_instrument_bootstrap,
    run_news_rss_event_enrichment,
)
from stockanalysis.ingest.news.eval import DEFAULT_DATASET_PATH, run_news_ai_eval
from stockanalysis.ingest.news.translation import run_news_rss_translation
from stockanalysis.operations.artifact_runner import run_data_operation_artifact_command
from stockanalysis.operations.cadence import build_data_operations_cadence_report
from stockanalysis.operations.cycle_ai_quality_audit import run_cycle_ai_quality_audit
from stockanalysis.operations.env_file import merged_env_with_file
from stockanalysis.operations.env_readiness import check_data_operations_runtime_env
from stockanalysis.operations.hosted_runtime_decision import (
    build_hosted_database_runtime_decision,
    render_hosted_database_runtime_decision_markdown,
)
from stockanalysis.operations.local_runtime_status import (
    DEFAULT_FRONTEND_API_URL,
    DEFAULT_LOCAL_RUNTIME_ROOT,
    DEFAULT_NEXT_COCKPIT_URL,
    build_local_first_runtime_status_report,
)
from stockanalysis.operations.local_ingest_worker import run_local_ingest_worker
from stockanalysis.operations.manual_local_ingest_smoke import (
    DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS,
    build_manual_local_ingest_smoke_report,
)
from stockanalysis.operations.manual_host_scheduler_activation_approval import (
    build_manual_host_scheduler_activation_explicit_approval_report,
)
from stockanalysis.operations.manual_host_scheduler_activation_preflight import (
    build_manual_host_scheduler_activation_preflight_report,
)
from stockanalysis.operations.market_price_free_backfill import (
    run_market_price_daily_from_env,
    run_market_price_free_backfill,
)
from stockanalysis.operations.news_rss_feed_runner import (
    NEWS_RSS_FEED_CONFIG_ENV,
    build_news_rss_config_report,
    run_news_rss_configured_feeds,
)
from stockanalysis.operations.operating_data_orchestrator import (
    OPERATING_DATA_RUN_PROFILE_IDS,
    build_operating_data_run_report,
)
from stockanalysis.operations.path_policy import resolve_existing_file, resolve_output_path
from stockanalysis.operations.report_io import load_json_object, print_json, write_json_report
from stockanalysis.operations.scheduler_activation_execution_decision import (
    build_data_operations_live_scheduler_host_activation_execution_decision_report,
)
from stockanalysis.operations.scheduler_activation_execution_final_preflight import (
    build_data_operations_live_scheduler_host_activation_execution_final_preflight_report,
)
from stockanalysis.operations.scheduler_activation_execution import (
    build_data_operations_live_scheduler_host_activation_execution_report,
)
from stockanalysis.operations.server_scheduler_invocation import (
    DEFAULT_SERVER_SCHEDULER_JOB_NAME,
    DEFAULT_SERVER_SCHEDULER_SCHEDULE,
    SERVER_SCHEDULER_TARGETS,
    build_server_scheduler_invocation_plan,
    render_server_scheduler_invocation_markdown,
)
from stockanalysis.operations.server_scheduler_deployment_decision import (
    build_server_scheduler_deployment_target_decision,
    render_server_scheduler_deployment_target_decision_markdown,
)
from stockanalysis.operations.operating_data_profile_scheduler import (
    DEFAULT_PROFILE_SCHEDULER_JOB_NAME,
    build_operating_data_profile_scheduler_invocation_plan,
    build_operating_data_profile_scheduler_status_report,
    render_operating_data_profile_scheduler_invocation_markdown,
)
from stockanalysis.ai.cycle_graph_context import run_cycle_graph_context_summary
from stockanalysis.signal.cycle_hierarchy_snapshot_v2 import run_cycle_hierarchy_snapshot_v2
from stockanalysis.signal.hierarchical_impact_propagation import run_hierarchical_impact_propagation
from stockanalysis.signal.macro_event_propagation import run_macro_event_propagation
from stockanalysis.trading.paper_safety_bootstrap import (
    PaperSafetyBootstrapConfig,
    decimal_from_cli,
    run_paper_safety_bootstrap_config,
)
from stockanalysis.trading.paper_validation import run_paper_validation_audit


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
EVENT_INTELLIGENCE_DATA_HEALTH_PIPELINE_NAME = "event_intelligence_llm_extract"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-operations",
        description="Data operations backend orchestration CLI.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    cadence = subparsers.add_parser("cadence", help="Print the data operations cadence registry.")
    cadence.add_argument("--cadence", choices=("intraday", "daily", "weekly", "monthly"))
    cadence.set_defaults(handler=_handle_cadence)

    run = subparsers.add_parser("run", help="Run a known data operation command with stdout/stderr artifacts.")
    run.add_argument("--job-id", required=True)
    run.add_argument("--artifact-root")
    run.add_argument("--timeout-seconds", type=int, default=3600)
    run.add_argument("command_argv", nargs=argparse.REMAINDER)
    run.set_defaults(handler=_handle_run)

    env_readiness = subparsers.add_parser(
        "env-readiness",
        help="Validate repo-outside data operations runtime env readiness.",
    )
    env_readiness.add_argument("--env-file")
    env_readiness.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    env_readiness.set_defaults(handler=_handle_env_readiness)

    local_runtime_status = subparsers.add_parser(
        "local-runtime-status",
        help="Print a secret-free local-first runtime status report without starting services.",
    )
    local_runtime_status.add_argument("--runtime-root", default=str(DEFAULT_LOCAL_RUNTIME_ROOT))
    local_runtime_status.add_argument("--frontend-api-env-file")
    local_runtime_status.add_argument("--data-operations-env-file")
    local_runtime_status.add_argument("--frontend-api-url", default=DEFAULT_FRONTEND_API_URL)
    local_runtime_status.add_argument("--next-url", default=DEFAULT_NEXT_COCKPIT_URL)
    local_runtime_status.add_argument("--http-timeout-seconds", type=float, default=2.0)
    local_runtime_status.add_argument("--skip-http-probes", action="store_true")
    local_runtime_status.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    local_runtime_status.set_defaults(handler=_handle_local_runtime_status)

    manual_local_ingest_smoke = subparsers.add_parser(
        "manual-local-ingest-smoke",
        help="Preview or execute market/news/AI local ingest smoke jobs through the artifact runner.",
    )
    manual_local_ingest_smoke.add_argument("--runtime-root", default=str(DEFAULT_LOCAL_RUNTIME_ROOT))
    manual_local_ingest_smoke.add_argument("--data-operations-env-file")
    manual_local_ingest_smoke.add_argument("--artifact-root")
    manual_local_ingest_smoke.add_argument(
        "--job-id",
        action="append",
        choices=DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS,
        help="Limit smoke to a known job. Repeat for multiple jobs.",
    )
    manual_local_ingest_smoke.add_argument("--execute", action="store_true")
    manual_local_ingest_smoke.add_argument(
        "--output",
        help="Write the secret-free smoke summary JSON to a repo-outside path for /data-health visibility.",
    )
    manual_local_ingest_smoke.add_argument("--timeout-seconds", type=int, default=1800)
    manual_local_ingest_smoke.add_argument("--python-executable")
    manual_local_ingest_smoke.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    manual_local_ingest_smoke.set_defaults(handler=_handle_manual_local_ingest_smoke)

    local_ingest_worker = subparsers.add_parser(
        "local-ingest-worker-run",
        help="Run bounded local market/news/AI ingest worker cycles without host scheduler mutation.",
    )
    local_ingest_worker.add_argument("--runtime-root", default=str(DEFAULT_LOCAL_RUNTIME_ROOT))
    local_ingest_worker.add_argument("--data-operations-env-file")
    local_ingest_worker.add_argument("--artifact-root")
    local_ingest_worker.add_argument(
        "--job-id",
        action="append",
        choices=DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS,
        help="Limit worker to a known job. Repeat for multiple jobs.",
    )
    local_ingest_worker.add_argument("--execute", action="store_true")
    local_ingest_worker.add_argument("--max-cycles", type=int, default=1)
    local_ingest_worker.add_argument("--interval-seconds", type=float, default=0.0)
    local_ingest_worker.add_argument("--timeout-seconds", type=int, default=1800)
    local_ingest_worker.add_argument("--python-executable")
    local_ingest_worker.add_argument(
        "--smoke-output",
        help="Write each latest manual-local-ingest-smoke summary to a repo-outside path for /data-health visibility.",
    )
    local_ingest_worker.add_argument("--output", help="Write the secret-free worker summary JSON to a repo-outside path.")
    local_ingest_worker.set_defaults(stop_on_failure=True)
    local_ingest_worker.add_argument("--continue-on-failure", dest="stop_on_failure", action="store_false")
    local_ingest_worker.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    local_ingest_worker.set_defaults(handler=_handle_local_ingest_worker_run)

    operating_data_run = subparsers.add_parser(
        "operating-data-run",
        help="Preview or execute the full operating-data alignment cycle through backend boundaries.",
    )
    operating_data_run.add_argument("--runtime-root", default=str(DEFAULT_LOCAL_RUNTIME_ROOT))
    operating_data_run.add_argument("--data-operations-env-file", required=True)
    operating_data_run.add_argument("--artifact-root")
    operating_data_run.add_argument("--profile", choices=OPERATING_DATA_RUN_PROFILE_IDS, default="full-recovery")
    operating_data_run.add_argument("--execute", action="store_true")
    operating_data_run.add_argument("--output")
    operating_data_run.add_argument("--timeout-seconds", type=int, default=3600)
    operating_data_run.add_argument("--python-executable")
    operating_data_run.add_argument("--portfolio-name", default="Long Term Paper")
    operating_data_run.add_argument("--strategy-name", default="long_term_core")
    operating_data_run.add_argument("--horizon-type", default="long_term")
    operating_data_run.add_argument("--market-code", default="US")
    operating_data_run.add_argument("--universe-version")
    operating_data_run.add_argument("--as-of-date")
    operating_data_run.add_argument("--provider")
    operating_data_run.add_argument("--daily-budget", type=int, default=24)
    operating_data_run.add_argument("--max-requests-per-run", type=int, default=4)
    operating_data_run.add_argument("--throttle-seconds", type=float, default=1.0)
    operating_data_run.add_argument("--outputsize", default="100")
    operating_data_run.add_argument("--portfolio-notional", default="100000")
    operating_data_run.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    operating_data_run.set_defaults(handler=_handle_operating_data_run)

    server_scheduler_invocation = subparsers.add_parser(
        "server-scheduler-invocation-plan",
        help="Build a secret-free server-side scheduler invocation packet without deploying a scheduler.",
    )
    server_scheduler_invocation.add_argument("--target", choices=SERVER_SCHEDULER_TARGETS, required=True)
    server_scheduler_invocation.add_argument("--schedule", default=DEFAULT_SERVER_SCHEDULER_SCHEDULE)
    server_scheduler_invocation.add_argument("--job-name", default=DEFAULT_SERVER_SCHEDULER_JOB_NAME)
    server_scheduler_invocation.add_argument("--runtime-root", default=str(DEFAULT_LOCAL_RUNTIME_ROOT))
    server_scheduler_invocation.add_argument("--data-operations-env-file", required=True)
    server_scheduler_invocation.add_argument("--worker-output", required=True)
    server_scheduler_invocation.add_argument("--smoke-output", required=True)
    server_scheduler_invocation.add_argument("--artifact-root")
    server_scheduler_invocation.add_argument(
        "--job-id",
        action="append",
        choices=DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS,
        help="Limit worker to a known job. Repeat for multiple jobs.",
    )
    server_scheduler_invocation.add_argument("--worker-execute", action="store_true")
    server_scheduler_invocation.add_argument("--max-cycles", type=int, default=1)
    server_scheduler_invocation.add_argument("--interval-seconds", type=float, default=0.0)
    server_scheduler_invocation.add_argument("--timeout-seconds", type=int, default=1800)
    server_scheduler_invocation.add_argument("--python-executable")
    server_scheduler_invocation.add_argument("--output")
    server_scheduler_invocation.add_argument("--markdown-output")
    server_scheduler_invocation.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    server_scheduler_invocation.set_defaults(handler=_handle_server_scheduler_invocation_plan)

    operating_data_profile_scheduler_invocation = subparsers.add_parser(
        "operating-data-profile-scheduler-invocation-plan",
        help="Build a secret-free operating-data profile scheduler invocation packet without deploying a scheduler.",
    )
    operating_data_profile_scheduler_invocation.add_argument("--target", choices=SERVER_SCHEDULER_TARGETS, required=True)
    operating_data_profile_scheduler_invocation.add_argument("--runtime-root", default=str(DEFAULT_LOCAL_RUNTIME_ROOT))
    operating_data_profile_scheduler_invocation.add_argument("--data-operations-env-file", required=True)
    operating_data_profile_scheduler_invocation.add_argument("--profile-output-root")
    operating_data_profile_scheduler_invocation.add_argument(
        "--manifest-output-root",
        help="Optional repo-outside directory path to write profile scheduler manifest files.",
    )
    operating_data_profile_scheduler_invocation.add_argument(
        "--profile-id",
        dest="profile_ids",
        action="append",
        help="Limit to one or more profile IDs. Repeat for multiple.",
    )
    operating_data_profile_scheduler_invocation.add_argument("--include-full-recovery", action="store_true")
    operating_data_profile_scheduler_invocation.add_argument("--schedule", help="Override schedule for all selected profiles.")
    operating_data_profile_scheduler_invocation.add_argument("--timeout-seconds", type=int, default=3600)
    operating_data_profile_scheduler_invocation.add_argument("--python-executable")
    operating_data_profile_scheduler_invocation.add_argument(
        "--systemd-user",
        help="Optional systemd service User= value for generated systemd profile manifests.",
    )
    operating_data_profile_scheduler_invocation.add_argument(
        "--systemd-group",
        help="Optional systemd service Group= value for generated systemd profile manifests.",
    )
    operating_data_profile_scheduler_invocation.add_argument(
        "--systemd-home",
        help=(
            "Optional absolute home path for generated systemd profile manifests. "
            "When set, HOME, CODEX_HOME, and XDG_CONFIG_HOME are rendered for the service."
        ),
    )
    operating_data_profile_scheduler_invocation.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Render child operating-data-run commands with --execute. "
            "This command still only writes invocation packets and does not deploy or run them."
        ),
    )
    operating_data_profile_scheduler_invocation.add_argument("--job-name", default=DEFAULT_PROFILE_SCHEDULER_JOB_NAME)
    operating_data_profile_scheduler_invocation.add_argument("--output")
    operating_data_profile_scheduler_invocation.add_argument("--markdown-output")
    operating_data_profile_scheduler_invocation.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    operating_data_profile_scheduler_invocation.set_defaults(handler=_handle_operating_data_profile_scheduler_invocation_plan)

    operating_data_profile_scheduler_status = subparsers.add_parser(
        "operating-data-profile-scheduler-status-report",
        help="Read systemd profile scheduler status and write a secret-free status report.",
    )
    operating_data_profile_scheduler_status.add_argument(
        "--profile-id",
        dest="profile_ids",
        action="append",
        help="Limit to one or more profile IDs. Repeat for multiple.",
    )
    operating_data_profile_scheduler_status.add_argument("--job-name", default="stockanalysis-operating-data")
    operating_data_profile_scheduler_status.add_argument("--output")
    operating_data_profile_scheduler_status.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    operating_data_profile_scheduler_status.set_defaults(handler=_handle_operating_data_profile_scheduler_status_report)

    server_scheduler_decision = subparsers.add_parser(
        "server-scheduler-deployment-target-decision",
        help="Decide a zero-budget scheduler deployment target without deploying a scheduler.",
    )
    server_scheduler_decision.add_argument("--repo-visibility", choices=("public", "private"), default="public")
    server_scheduler_decision.set_defaults(zero_budget_required=True)
    server_scheduler_decision.add_argument("--zero-budget-required", dest="zero_budget_required", action="store_true")
    server_scheduler_decision.add_argument("--allow-paid", dest="zero_budget_required", action="store_false")
    server_scheduler_decision.add_argument("--hosted-database-configured", action="store_true")
    server_scheduler_decision.add_argument("--runtime-host-available", action="store_true")
    server_scheduler_decision.add_argument("--allow-mac-host-scheduler", dest="mac_host_scheduler_allowed", action="store_true")
    server_scheduler_decision.add_argument("--kubernetes-cluster-available", action="store_true")
    server_scheduler_decision.add_argument("--managed-scheduler-free-tier-confirmed", action="store_true")
    server_scheduler_decision.set_defaults(github_actions_allowed=True)
    server_scheduler_decision.add_argument("--github-actions-allowed", dest="github_actions_allowed", action="store_true")
    server_scheduler_decision.add_argument("--no-github-actions", dest="github_actions_allowed", action="store_false")
    server_scheduler_decision.add_argument("--output")
    server_scheduler_decision.add_argument("--markdown-output")
    server_scheduler_decision.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    server_scheduler_decision.set_defaults(handler=_handle_server_scheduler_deployment_target_decision)

    hosted_database_runtime_decision = subparsers.add_parser(
        "hosted-database-runtime-decision",
        help="Decide the zero-budget hosted DB/runtime path without provisioning anything.",
    )
    hosted_database_runtime_decision.add_argument("--repo-visibility", choices=("public", "private"), default="public")
    hosted_database_runtime_decision.set_defaults(zero_budget_required=True)
    hosted_database_runtime_decision.add_argument(
        "--zero-budget-required",
        dest="zero_budget_required",
        action="store_true",
    )
    hosted_database_runtime_decision.add_argument("--allow-paid", dest="zero_budget_required", action="store_false")
    hosted_database_runtime_decision.add_argument("--hosted-database-configured", action="store_true")
    hosted_database_runtime_decision.add_argument("--existing-runtime-host-available", action="store_true")
    hosted_database_runtime_decision.set_defaults(supabase_free_project_available=True)
    hosted_database_runtime_decision.add_argument(
        "--supabase-free-project-available",
        dest="supabase_free_project_available",
        action="store_true",
    )
    hosted_database_runtime_decision.add_argument(
        "--no-supabase-free-project",
        dest="supabase_free_project_available",
        action="store_false",
    )
    hosted_database_runtime_decision.add_argument("--local-only-accepted", action="store_true")
    hosted_database_runtime_decision.set_defaults(github_actions_allowed=True)
    hosted_database_runtime_decision.add_argument(
        "--github-actions-allowed",
        dest="github_actions_allowed",
        action="store_true",
    )
    hosted_database_runtime_decision.add_argument("--no-github-actions", dest="github_actions_allowed", action="store_false")
    hosted_database_runtime_decision.add_argument("--output")
    hosted_database_runtime_decision.add_argument("--markdown-output")
    hosted_database_runtime_decision.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    hosted_database_runtime_decision.set_defaults(handler=_handle_hosted_database_runtime_decision)

    market_price_free_backfill = subparsers.add_parser(
        "market-price-free-backfill-run",
        help="Run a free-tier-safe market price watchlist backfill with a daily provider budget ledger.",
    )
    market_price_free_backfill.add_argument("--watchlist", required=True)
    market_price_free_backfill.add_argument("--ledger", required=True)
    market_price_free_backfill.add_argument("--provider", default="alpha_vantage")
    market_price_free_backfill.add_argument("--env-file")
    market_price_free_backfill.add_argument("--daily-budget", type=int, default=25)
    market_price_free_backfill.add_argument("--max-requests-per-run", type=int, default=25)
    market_price_free_backfill.add_argument("--throttle-seconds", type=float, default=1.0)
    market_price_free_backfill.add_argument("--fixtures-dir")
    market_price_free_backfill.add_argument("--outputsize")
    market_price_free_backfill.add_argument("--budget-date")
    market_price_free_backfill.add_argument("--skip-if-fresh", action="store_true")
    market_price_free_backfill.add_argument(
        "--freshness-date",
        help="Target freshness date in YYYY-MM-DD format. Defaults to runtime date when --skip-if-fresh is used.",
    )
    market_price_free_backfill.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    market_price_free_backfill.set_defaults(handler=_handle_market_price_free_backfill_run)

    market_price_daily = subparsers.add_parser(
        "market-price-daily-run",
        help="Run the scheduler-friendly market price daily job from repo-outside env defaults.",
    )
    market_price_daily.add_argument("--env-file")
    market_price_daily.add_argument("--provider")
    market_price_daily.add_argument("--daily-budget", type=int)
    market_price_daily.add_argument("--max-requests-per-run", type=int)
    market_price_daily.add_argument("--throttle-seconds", type=float)
    market_price_daily.add_argument("--outputsize")
    market_price_daily.add_argument("--budget-date")
    market_price_daily.set_defaults(skip_if_fresh=True)
    market_price_daily.add_argument("--skip-if-fresh", dest="skip_if_fresh", action="store_true")
    market_price_daily.add_argument("--no-skip-if-fresh", dest="skip_if_fresh", action="store_false")
    market_price_daily.add_argument(
        "--freshness-date",
        help=(
            "Target freshness date in YYYY-MM-DD format. Defaults to "
            "DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE or the latest completed US market day."
        ),
    )
    market_price_daily.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    market_price_daily.set_defaults(handler=_handle_market_price_daily_run)

    news_rss_config_report = subparsers.add_parser(
        "news-rss-config-report",
        help="Print a sanitized report for a repo-outside free RSS feed config.",
    )
    news_rss_config_report.add_argument("--feed-config")
    news_rss_config_report.add_argument("--env-file")
    news_rss_config_report.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_rss_config_report.set_defaults(handler=_handle_news_rss_config_report)

    news_rss_daily = subparsers.add_parser(
        "news-rss-daily-run",
        help="Run configured free RSS/Atom feeds through the canonical news-rss-upsert boundary.",
    )
    news_rss_daily.add_argument("--feed-config")
    news_rss_daily.add_argument("--feed-name", action="append", default=[])
    news_rss_daily.add_argument("--env-file")
    news_rss_daily.add_argument("--dry-run", action="store_true")
    news_rss_daily.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_rss_daily.set_defaults(handler=_handle_news_rss_daily_run)

    news_rss_enrich = subparsers.add_parser(
        "news-rss-enrich-run",
        help="Run free local rule-based enrichment for pending RSS news events.",
    )
    news_rss_enrich.add_argument("--env-file")
    news_rss_enrich.add_argument("--limit", type=int, default=50)
    news_rss_enrich.add_argument("--dry-run", action="store_true")
    news_rss_enrich.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_rss_enrich.set_defaults(handler=_handle_news_rss_enrich_run)

    news_missing_instrument_bootstrap = subparsers.add_parser(
        "news-missing-instrument-bootstrap-run",
        help="Bootstrap SEC-verified listed instruments for explicit news tickers missing from ref.instrument.",
    )
    news_missing_instrument_bootstrap.add_argument("--env-file")
    news_missing_instrument_bootstrap.add_argument("--limit", type=int, default=100)
    news_missing_instrument_bootstrap.add_argument("--company-tickers-json")
    news_missing_instrument_bootstrap.add_argument("--exchange", action="append", default=[])
    news_missing_instrument_bootstrap.add_argument("--dry-run", action="store_true")
    news_missing_instrument_bootstrap.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_missing_instrument_bootstrap.set_defaults(handler=_handle_news_missing_instrument_bootstrap_run)

    news_rss_cluster_evidence = subparsers.add_parser(
        "news-rss-cluster-evidence-run",
        help="Persist free local RSS news cluster summaries as auditable AI evidence artifacts.",
    )
    news_rss_cluster_evidence.add_argument("--env-file")
    news_rss_cluster_evidence.add_argument("--as-of-date")
    news_rss_cluster_evidence.add_argument("--event-limit", type=int, default=100)
    news_rss_cluster_evidence.add_argument("--max-clusters", type=int, default=4)
    news_rss_cluster_evidence.add_argument("--dry-run", action="store_true")
    news_rss_cluster_evidence.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_rss_cluster_evidence.set_defaults(handler=_handle_news_rss_cluster_evidence_run)

    news_rss_translation = subparsers.add_parser(
        "news-rss-translation-run",
        help="Run offline Codex OAuth Korean translation for RSS source documents.",
    )
    news_rss_translation.add_argument("--env-file")
    news_rss_translation.add_argument("--as-of-date")
    news_rss_translation.add_argument("--limit", type=int, default=20)
    news_rss_translation.add_argument("--provider", choices=("fixture", "codex_oauth"), default=CODEX_OAUTH_PROVIDER)
    news_rss_translation.add_argument("--model-name", default="codex-cli-default")
    news_rss_translation.add_argument("--reasoning-effort", default="low")
    news_rss_translation.add_argument("--max-input-chars", type=int, default=4000)
    news_rss_translation.add_argument("--llm-output-json")
    news_rss_translation.add_argument("--execute", action="store_true")
    news_rss_translation.add_argument("--dry-run", action="store_true")
    news_rss_translation.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_rss_translation.set_defaults(handler=_handle_news_rss_translation_run)

    news_rss_ai_extract = subparsers.add_parser(
        "news-rss-ai-extract-run",
        help="Run offline Codex OAuth RSS news AI extraction with validator-gated canonical impact writes.",
    )
    news_rss_ai_extract.add_argument("--env-file")
    news_rss_ai_extract.add_argument("--as-of-date")
    news_rss_ai_extract.add_argument("--limit", type=int, default=10)
    news_rss_ai_extract.add_argument("--provider", choices=("fixture", "codex_oauth"), default=CODEX_OAUTH_PROVIDER)
    news_rss_ai_extract.add_argument("--model-name", default="codex-cli-default")
    news_rss_ai_extract.add_argument("--reasoning-effort", default="low")
    news_rss_ai_extract.add_argument("--max-input-chars", type=int, default=6000)
    news_rss_ai_extract.add_argument("--min-confidence", type=float, default=0.72)
    news_rss_ai_extract.add_argument("--llm-output-json")
    news_rss_ai_extract.add_argument("--execute", action="store_true")
    news_rss_ai_extract.add_argument("--dry-run", action="store_true")
    news_rss_ai_extract.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_rss_ai_extract.set_defaults(handler=_handle_news_rss_ai_extract_run)

    news_ai_eval = subparsers.add_parser(
        "news-ai-eval-run",
        help="Score fixture/gold news AI extraction cases and optionally store metrics in ai.eval_run.",
    )
    news_ai_eval.add_argument("--env-file")
    news_ai_eval.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    news_ai_eval.add_argument("--provider", choices=("fixture",), default="fixture")
    news_ai_eval.add_argument("--model-name", default="news-ai-eval-fixture-v1")
    news_ai_eval.add_argument("--min-confidence", type=float, default=0.72)
    news_ai_eval.add_argument("--execute", action="store_true")
    news_ai_eval.add_argument("--dry-run", action="store_true")
    news_ai_eval.add_argument("--output")
    news_ai_eval.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    news_ai_eval.set_defaults(handler=_handle_news_ai_eval_run)

    macro_event_propagation = subparsers.add_parser(
        "macro-event-propagation-run",
        help="Propagate macro/theme news events to instruments through factor exposure rows.",
    )
    macro_event_propagation.add_argument("--env-file")
    macro_event_propagation.add_argument("--as-of-date", required=True)
    macro_event_propagation.add_argument("--limit", type=int, default=200)
    macro_event_propagation.add_argument("--execute", action="store_true")
    macro_event_propagation.add_argument("--dry-run", action="store_true")
    macro_event_propagation.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    macro_event_propagation.set_defaults(handler=_handle_macro_event_propagation_run)

    hierarchical_impact_propagation = subparsers.add_parser(
        "hierarchical-impact-propagation-run",
        help="Propagate macro/domain/theme news events through classification graph paths to exposed instruments.",
    )
    hierarchical_impact_propagation.add_argument("--env-file")
    hierarchical_impact_propagation.add_argument("--as-of-date", required=True)
    hierarchical_impact_propagation.add_argument("--limit", type=int, default=200)
    hierarchical_impact_propagation.add_argument("--max-depth", type=int, default=3)
    hierarchical_impact_propagation.add_argument("--decay-per-hop", default="0.8500")
    hierarchical_impact_propagation.add_argument("--execute", action="store_true")
    hierarchical_impact_propagation.add_argument("--dry-run", action="store_true")
    hierarchical_impact_propagation.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    hierarchical_impact_propagation.set_defaults(handler=_handle_hierarchical_impact_propagation_run)

    cycle_hierarchy_snapshot_v2 = subparsers.add_parser(
        "cycle-hierarchy-snapshot-v2-run",
        help="Create node-level hierarchical cycle state snapshots from base cycles and propagated evidence.",
    )
    cycle_hierarchy_snapshot_v2.add_argument("--env-file")
    cycle_hierarchy_snapshot_v2.add_argument("--as-of-date", required=True)
    cycle_hierarchy_snapshot_v2.add_argument("--execute", action="store_true")
    cycle_hierarchy_snapshot_v2.add_argument("--dry-run", action="store_true")
    cycle_hierarchy_snapshot_v2.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    cycle_hierarchy_snapshot_v2.set_defaults(handler=_handle_cycle_hierarchy_snapshot_v2_run)

    cycle_graph_context_summary = subparsers.add_parser(
        "cycle-graph-context-summary-run",
        help="Build reusable Postgres graph context summaries for macro/domain/theme cycle nodes.",
    )
    cycle_graph_context_summary.add_argument("--env-file")
    cycle_graph_context_summary.add_argument("--as-of-date", required=True)
    cycle_graph_context_summary.add_argument("--node-code", action="append")
    cycle_graph_context_summary.add_argument("--limit", type=int, default=12)
    cycle_graph_context_summary.add_argument("--max-nodes", type=int, default=50)
    cycle_graph_context_summary.add_argument("--execute", action="store_true")
    cycle_graph_context_summary.add_argument("--dry-run", action="store_true")
    cycle_graph_context_summary.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    cycle_graph_context_summary.set_defaults(handler=_handle_cycle_graph_context_summary_run)

    cycle_ai_quality_audit = subparsers.add_parser(
        "cycle-ai-quality-audit-run",
        help="Audit RSS, Korean translation, AI extraction, propagation, cycle, recommendation, and paper quality.",
    )
    cycle_ai_quality_audit.add_argument("--env-file")
    cycle_ai_quality_audit.add_argument("--as-of-date", required=True)
    cycle_ai_quality_audit.add_argument("--lookback-days", type=int, default=30)
    cycle_ai_quality_audit.add_argument("--execute", action="store_true")
    cycle_ai_quality_audit.add_argument("--dry-run", action="store_true")
    cycle_ai_quality_audit.add_argument("--output")
    cycle_ai_quality_audit.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    cycle_ai_quality_audit.set_defaults(handler=_handle_cycle_ai_quality_audit_run)

    paper_validation_audit = subparsers.add_parser(
        "paper-validation-audit-run",
        help="Write broker-free paper validation and order intent audit rows from the frontend paper preview.",
    )
    paper_validation_audit.add_argument("--env-file")
    paper_validation_audit.add_argument("--source", choices=("live", "fixture", "auto"), default="live")
    paper_validation_audit.add_argument("--as-of-date")
    paper_validation_audit.add_argument("--portfolio-notional", default="100000")
    paper_validation_audit.add_argument("--created-by", default="paper-validation-audit-run")
    paper_validation_audit.add_argument("--human-approved", action="store_true")
    paper_validation_audit.add_argument("--dry-run", action="store_true")
    paper_validation_audit.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    paper_validation_audit.set_defaults(handler=_handle_paper_validation_audit_run)

    paper_safety_bootstrap = subparsers.add_parser(
        "paper-safety-bootstrap-config",
        help="Upsert simulated paper broker/account/order-limit safety rows without enabling broker submission.",
    )
    paper_safety_bootstrap.add_argument("--env-file")
    paper_safety_bootstrap.add_argument("--portfolio-name", default="Long Term Paper")
    paper_safety_bootstrap.add_argument("--broker-code", default="simulated_paper")
    paper_safety_bootstrap.add_argument("--account-ref", default="paper-account-long-term")
    paper_safety_bootstrap.add_argument("--policy-name", default="long-term-paper-default")
    paper_safety_bootstrap.add_argument("--max-single-order-notional", default="50000")
    paper_safety_bootstrap.add_argument("--max-daily-order-notional", default="100000")
    paper_safety_bootstrap.add_argument("--max-single-order-weight-delta", default="0.20")
    paper_safety_bootstrap.add_argument("--max-post-trade-symbol-weight", default="0.40")
    paper_safety_bootstrap.add_argument("--min-cash-buffer-weight", default="0.02")
    paper_safety_bootstrap.add_argument("--created-by", default="paper-safety-bootstrap-config")
    paper_safety_bootstrap.add_argument("--dry-run", action="store_true")
    paper_safety_bootstrap.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    paper_safety_bootstrap.set_defaults(handler=_handle_paper_safety_bootstrap_config)

    execution_decision = subparsers.add_parser(
        "host-activation-execution-decision",
        help="Validate approve/deny host activation execution decisions without host mutation.",
    )
    execution_decision.add_argument("--execution-request-report", required=True)
    execution_decision.add_argument("--decision-record")
    execution_decision.add_argument("--output")
    execution_decision.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    execution_decision.set_defaults(handler=_handle_host_activation_execution_decision)

    execution_final_preflight = subparsers.add_parser(
        "host-activation-execution-final-preflight",
        help="Revalidate approved host activation execution evidence and fresh runtime readiness without host mutation.",
    )
    execution_final_preflight.add_argument("--execution-decision-report", required=True)
    execution_final_preflight.add_argument("--execution-request-report")
    execution_final_preflight.add_argument("--host-activation-plan-report")
    execution_final_preflight.add_argument("--env-file", required=True)
    execution_final_preflight.add_argument("--output-dir", required=True)
    execution_final_preflight.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    execution_final_preflight.set_defaults(handler=_handle_host_activation_execution_final_preflight)

    host_activation_execution = subparsers.add_parser(
        "host-activation-execution",
        help="Build the host activation execution gate report without executing host mutation.",
    )
    host_activation_execution.add_argument("--execution-final-preflight-report", required=True)
    host_activation_execution.add_argument("--confirmation-record")
    host_activation_execution.add_argument("--output")
    host_activation_execution.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    host_activation_execution.set_defaults(handler=_handle_host_activation_execution)

    manual_host_activation_approval = subparsers.add_parser(
        "manual-host-scheduler-activation-explicit-approval",
        help="Build the exact host command approval packet without executing host mutation.",
    )
    manual_host_activation_approval.add_argument("--host-activation-execution-report", required=True)
    manual_host_activation_approval.add_argument("--approval-record")
    manual_host_activation_approval.add_argument("--output")
    manual_host_activation_approval.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    manual_host_activation_approval.set_defaults(handler=_handle_manual_host_scheduler_activation_explicit_approval)

    manual_host_activation_preflight = subparsers.add_parser(
        "manual-host-scheduler-activation-preflight",
        help="Preflight approved exact host commands and runtime env without executing host mutation.",
    )
    manual_host_activation_preflight.add_argument("--manual-approval-report", required=True)
    manual_host_activation_preflight.add_argument("--env-file", required=True)
    manual_host_activation_preflight.add_argument("--output-dir", required=True)
    manual_host_activation_preflight.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    manual_host_activation_preflight.set_defaults(handler=_handle_manual_host_scheduler_activation_preflight)

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    try:
        return int(args.handler(args, stdout=out))
    except (FileNotFoundError, ValueError) as exc:
        err.write(str(exc) + "\n")
        return 1


def _handle_cadence(args: argparse.Namespace, *, stdout: TextIO) -> int:
    print_json(build_data_operations_cadence_report(cadence=args.cadence), stdout=stdout, sort_keys=False)
    return 0


def _handle_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    command_argv = list(args.command_argv)
    if command_argv and command_argv[0] == "--":
        command_argv = command_argv[1:]
    result = run_data_operation_artifact_command(
        job_id=args.job_id,
        artifact_root=args.artifact_root,
        command_argv=command_argv,
        timeout_seconds=args.timeout_seconds,
    )
    print_json(result, stdout=stdout, sort_keys=False)
    return int(result["exit_code"])


def _handle_env_readiness(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping = merged_env_with_file(args.env_file) if args.env_file else None
    report = check_data_operations_runtime_env(
        env=env_mapping,
        repo_root=args.repo_root,
        env_file=args.env_file,
    )
    print_json(report, stdout=stdout)
    return 0


def _handle_local_runtime_status(args: argparse.Namespace, *, stdout: TextIO) -> int:
    report = build_local_first_runtime_status_report(
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
        frontend_api_env_file=args.frontend_api_env_file,
        data_operations_env_file=args.data_operations_env_file,
        frontend_api_url=args.frontend_api_url,
        next_url=args.next_url,
        http_timeout_seconds=args.http_timeout_seconds,
        skip_http_probes=bool(args.skip_http_probes),
    )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_manual_local_ingest_smoke(args: argparse.Namespace, *, stdout: TextIO) -> int:
    report = build_manual_local_ingest_smoke_report(
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
        data_operations_env_file=args.data_operations_env_file,
        artifact_root=args.artifact_root,
        job_ids=tuple(args.job_id) if args.job_id else None,
        execute=bool(args.execute),
        timeout_seconds=args.timeout_seconds,
        python_executable=args.python_executable,
    )
    if args.output:
        output_path = resolve_output_path(
            args.output,
            label="manual local ingest smoke summary output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        write_json_report(report, output_path=output_path, stdout=stdout)
    else:
        print_json(report, stdout=stdout, sort_keys=False)
    return 1 if report.get("smoke_status") == "failed" else 0


def _handle_local_ingest_worker_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="local ingest worker summary output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    report = run_local_ingest_worker(
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
        data_operations_env_file=args.data_operations_env_file,
        artifact_root=args.artifact_root,
        job_ids=tuple(args.job_id) if args.job_id else None,
        execute=bool(args.execute),
        max_cycles=args.max_cycles,
        interval_seconds=args.interval_seconds,
        timeout_seconds=args.timeout_seconds,
        python_executable=args.python_executable,
        smoke_output_path=args.smoke_output,
        stop_on_failure=bool(args.stop_on_failure),
    )
    if output_path:
        write_json_report(report, output_path=output_path, stdout=stdout)
    else:
        print_json(report, stdout=stdout, sort_keys=False)
    return 1 if report.get("worker_status") == "failed" else 0


def _handle_operating_data_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="operating data run summary output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    report = build_operating_data_run_report(
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
        data_operations_env_file=args.data_operations_env_file,
        artifact_root=args.artifact_root,
        profile=args.profile,
        execute=bool(args.execute),
        timeout_seconds=args.timeout_seconds,
        python_executable=args.python_executable,
        portfolio_name=args.portfolio_name,
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        market_code=args.market_code,
        universe_version=args.universe_version,
        as_of_date=date.fromisoformat(args.as_of_date) if args.as_of_date else None,
        provider=args.provider,
        daily_budget=args.daily_budget,
        max_requests_per_run=args.max_requests_per_run,
        throttle_seconds=args.throttle_seconds,
        outputsize=args.outputsize,
        portfolio_notional=Decimal(args.portfolio_notional),
    )
    if output_path:
        write_json_report(report, output_path=output_path, stdout=stdout)
    else:
        print_json(report, stdout=stdout, sort_keys=False)
    return 1 if report.get("run_status") == "failed" else 0


def _handle_server_scheduler_invocation_plan(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="server scheduler invocation output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    markdown_output_path = (
        resolve_output_path(
            args.markdown_output,
            label="server scheduler invocation markdown output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.markdown_output
        else None
    )
    report = build_server_scheduler_invocation_plan(
        scheduler_target=args.target,
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
        data_operations_env_file=args.data_operations_env_file,
        worker_report_output=args.worker_output,
        smoke_output=args.smoke_output,
        artifact_root=args.artifact_root,
        job_ids=tuple(args.job_id) if args.job_id else None,
        worker_execute=bool(args.worker_execute),
        max_cycles=args.max_cycles,
        interval_seconds=args.interval_seconds,
        timeout_seconds=args.timeout_seconds,
        schedule=args.schedule,
        python_executable=args.python_executable,
        job_name=args.job_name,
    )
    if markdown_output_path is not None:
        markdown_output_path.write_text(render_server_scheduler_invocation_markdown(report), encoding="utf-8")
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_operating_data_profile_scheduler_invocation_plan(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="operating data profile scheduler output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    markdown_output_path = (
        resolve_output_path(
            args.markdown_output,
            label="operating data profile scheduler markdown output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.markdown_output
        else None
    )
    report = build_operating_data_profile_scheduler_invocation_plan(
        scheduler_target=args.target,
        repo_root=args.repo_root,
        runtime_root=args.runtime_root,
        data_operations_env_file=args.data_operations_env_file,
        profile_output_root=args.profile_output_root,
        manifest_output_root=args.manifest_output_root,
        profile_ids=tuple(args.profile_ids) if args.profile_ids else None,
        include_full_recovery=bool(args.include_full_recovery),
        schedule=args.schedule,
        timeout_seconds=args.timeout_seconds,
        python_executable=args.python_executable,
        execute=bool(args.execute),
        job_name=args.job_name,
        systemd_user=args.systemd_user,
        systemd_group=args.systemd_group,
        systemd_home=args.systemd_home,
    )
    if markdown_output_path is not None:
        markdown_output_path.write_text(
            render_operating_data_profile_scheduler_invocation_markdown(report),
            encoding="utf-8",
        )
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_operating_data_profile_scheduler_status_report(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="operating data profile scheduler status output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    report = build_operating_data_profile_scheduler_status_report(
        profile_ids=tuple(args.profile_ids) if args.profile_ids else None,
        job_name=args.job_name,
    )
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_server_scheduler_deployment_target_decision(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="server scheduler deployment target decision output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    markdown_output_path = (
        resolve_output_path(
            args.markdown_output,
            label="server scheduler deployment target decision markdown output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.markdown_output
        else None
    )
    report = build_server_scheduler_deployment_target_decision(
        repo_visibility=args.repo_visibility,
        zero_budget_required=bool(args.zero_budget_required),
        hosted_database_configured=bool(args.hosted_database_configured),
        runtime_host_available=bool(args.runtime_host_available),
        mac_host_scheduler_allowed=bool(args.mac_host_scheduler_allowed),
        kubernetes_cluster_available=bool(args.kubernetes_cluster_available),
        managed_scheduler_free_tier_confirmed=bool(args.managed_scheduler_free_tier_confirmed),
        github_actions_allowed=bool(args.github_actions_allowed),
    )
    if markdown_output_path is not None:
        markdown_output_path.write_text(
            render_server_scheduler_deployment_target_decision_markdown(report),
            encoding="utf-8",
        )
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_hosted_database_runtime_decision(args: argparse.Namespace, *, stdout: TextIO) -> int:
    output_path = (
        resolve_output_path(
            args.output,
            label="hosted database runtime decision output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.output
        else None
    )
    markdown_output_path = (
        resolve_output_path(
            args.markdown_output,
            label="hosted database runtime decision markdown output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        if args.markdown_output
        else None
    )
    report = build_hosted_database_runtime_decision(
        repo_visibility=args.repo_visibility,
        zero_budget_required=bool(args.zero_budget_required),
        hosted_database_configured=bool(args.hosted_database_configured),
        existing_runtime_host_available=bool(args.existing_runtime_host_available),
        supabase_free_project_available=bool(args.supabase_free_project_available),
        local_only_accepted=bool(args.local_only_accepted),
        github_actions_allowed=bool(args.github_actions_allowed),
    )
    if markdown_output_path is not None:
        markdown_output_path.write_text(render_hosted_database_runtime_decision_markdown(report), encoding="utf-8")
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_market_price_free_backfill_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    watchlist_path = resolve_existing_file(
        args.watchlist,
        label="market price free backfill watchlist",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    ledger_path = resolve_output_path(
        args.ledger,
        label="market price provider budget ledger",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    env_mapping: Mapping[str, str] | None = None
    if args.env_file:
        env_file_path = resolve_existing_file(
            args.env_file,
            label="data operations env file",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        env_mapping = merged_env_with_file(env_file_path)
    budget_date = None
    if args.budget_date:
        budget_date = date.fromisoformat(args.budget_date)
    freshness_date = date.fromisoformat(args.freshness_date) if args.freshness_date else None

    with _temporary_environ(env_mapping):
        report = run_market_price_free_backfill(
            config=RuntimeConfig.from_env(),
            watchlist_path=watchlist_path,
            ledger_path=ledger_path,
            provider=args.provider,
            budget_date=budget_date,
            daily_budget=args.daily_budget,
            max_requests_per_run=args.max_requests_per_run,
            throttle_seconds=args.throttle_seconds,
            fixtures_dir=args.fixtures_dir,
            outputsize=args.outputsize,
            skip_if_fresh=args.skip_if_fresh,
            freshness_date=freshness_date,
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0 if int(report.get("failed_symbol_count", 0)) == 0 else 1


def _handle_market_price_daily_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping: Mapping[str, str] | None = None
    if args.env_file:
        env_file_path = resolve_existing_file(
            args.env_file,
            label="data operations env file",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        env_mapping = merged_env_with_file(env_file_path)
    budget_date = date.fromisoformat(args.budget_date) if args.budget_date else None
    freshness_date = date.fromisoformat(args.freshness_date) if args.freshness_date else None

    with _temporary_environ(env_mapping):
        report = run_market_price_daily_from_env(
            config=RuntimeConfig.from_env(),
            provider=args.provider,
            budget_date=budget_date,
            daily_budget=args.daily_budget,
            max_requests_per_run=args.max_requests_per_run,
            throttle_seconds=args.throttle_seconds,
            outputsize=args.outputsize,
            skip_if_fresh=bool(args.skip_if_fresh),
            freshness_date=freshness_date,
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0 if int(report.get("failed_symbol_count", 0)) == 0 else 1


def _handle_news_rss_config_report(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    feed_config_path = _resolve_news_rss_feed_config_path(args.feed_config, env=env_mapping, repo_root=args.repo_root)
    report = build_news_rss_config_report(
        config_path=feed_config_path,
        repo_root=args.repo_root,
    )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_news_rss_daily_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    feed_config_path = _resolve_news_rss_feed_config_path(args.feed_config, env=env_mapping, repo_root=args.repo_root)

    with _temporary_environ(env_mapping):
        report = run_news_rss_configured_feeds(
            config=RuntimeConfig.from_env(),
            feed_config_path=feed_config_path,
            repo_root=args.repo_root,
            feed_names=tuple(args.feed_name),
            dry_run=bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0 if int(report.get("failed_feed_count", 0)) == 0 else 1


def _handle_news_rss_enrich_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    with _temporary_environ(env_mapping):
        report = run_news_rss_event_enrichment(
            config=RuntimeConfig.from_env(),
            limit=args.limit,
            dry_run=bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0 if int(report.get("failed_event_count", 0)) == 0 else 1


def _handle_news_missing_instrument_bootstrap_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    company_tickers_json = (
        str(resolve_existing_file(args.company_tickers_json, label="company tickers JSON", repo_root=args.repo_root))
        if args.company_tickers_json
        else None
    )
    with _temporary_environ(env_mapping):
        report = run_news_missing_instrument_bootstrap(
            config=RuntimeConfig.from_env(),
            limit=args.limit,
            company_tickers_json_path=company_tickers_json,
            exchanges=args.exchange or None,
            dry_run=bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_news_rss_cluster_evidence_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date) if args.as_of_date else None
    with _temporary_environ(env_mapping):
        report = run_news_rss_cluster_evidence(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            event_limit=args.event_limit,
            max_clusters=args.max_clusters,
            dry_run=bool(args.dry_run),
            pipeline_name=EVENT_INTELLIGENCE_DATA_HEALTH_PIPELINE_NAME,
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0 if int(report.get("failed_cluster_count", 0)) == 0 else 1


def _handle_news_rss_translation_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date) if args.as_of_date else None
    with _temporary_environ(env_mapping):
        report = run_news_rss_translation(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            limit=args.limit,
            provider=args.provider,
            model_name=args.model_name,
            reasoning_effort=args.reasoning_effort,
            max_input_chars=args.max_input_chars,
            execute=bool(args.execute) and not bool(args.dry_run),
            llm_output_json_path=args.llm_output_json,
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_news_rss_ai_extract_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date) if args.as_of_date else None
    with _temporary_environ(env_mapping):
        report = run_news_rss_ai_extract(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            limit=args.limit,
            provider=args.provider,
            model_name=args.model_name,
            reasoning_effort=args.reasoning_effort,
            max_input_chars=args.max_input_chars,
            min_confidence=args.min_confidence,
            execute=bool(args.execute) and not bool(args.dry_run),
            llm_output_json_path=args.llm_output_json,
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_news_ai_eval_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    dataset_path = resolve_existing_file(
        args.dataset_path,
        label="news AI eval dataset",
        repo_root=args.repo_root,
        require_repo_outside=False,
    )
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    with _temporary_environ(env_mapping):
        report = run_news_ai_eval(
            config=RuntimeConfig.from_env(),
            dataset_path=dataset_path,
            provider=args.provider,
            model_name=args.model_name,
            min_confidence=args.min_confidence,
            execute=bool(args.execute) and not bool(args.dry_run),
        )
    if args.output:
        output_path = resolve_output_path(
            args.output,
            label="news AI eval output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        write_json_report(report, output_path=output_path, stdout=stdout)
    else:
        print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_macro_event_propagation_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date)
    with _temporary_environ(env_mapping):
        report = run_macro_event_propagation(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            limit=args.limit,
            execute=bool(args.execute) and not bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_hierarchical_impact_propagation_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date)
    with _temporary_environ(env_mapping):
        report = run_hierarchical_impact_propagation(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            limit=args.limit,
            max_depth=args.max_depth,
            decay_per_hop=Decimal(args.decay_per_hop),
            execute=bool(args.execute) and not bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_cycle_hierarchy_snapshot_v2_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date)
    with _temporary_environ(env_mapping):
        report = run_cycle_hierarchy_snapshot_v2(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            execute=bool(args.execute) and not bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_cycle_graph_context_summary_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date)
    with _temporary_environ(env_mapping):
        report = run_cycle_graph_context_summary(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            node_codes=tuple(args.node_code or ()),
            limit=args.limit,
            max_nodes=args.max_nodes,
            execute=bool(args.execute) and not bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_cycle_ai_quality_audit_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    if bool(args.execute) and bool(args.dry_run):
        raise ValueError("--execute and --dry-run cannot be used together.")
    env_mapping = _load_optional_env_mapping(args.env_file, repo_root=args.repo_root)
    as_of_date = date.fromisoformat(args.as_of_date)
    with _temporary_environ(env_mapping):
        report = run_cycle_ai_quality_audit(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            lookback_days=args.lookback_days,
            execute=bool(args.execute) and not bool(args.dry_run),
        )
    if args.output:
        output_path = resolve_output_path(
            args.output,
            label="cycle AI quality audit output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        write_json_report(report, output_path=output_path, stdout=stdout)
    else:
        print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_paper_validation_audit_run(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping: Mapping[str, str] | None = None
    if args.env_file:
        env_file_path = resolve_existing_file(
            args.env_file,
            label="data operations env file",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        env_mapping = merged_env_with_file(env_file_path)
    as_of_date = date.fromisoformat(args.as_of_date) if args.as_of_date else None

    with _temporary_environ(env_mapping):
        report = run_paper_validation_audit(
            config=RuntimeConfig.from_env(),
            source=args.source,
            as_of_date=as_of_date,
            portfolio_notional=Decimal(args.portfolio_notional),
            created_by=args.created_by,
            human_approved=bool(args.human_approved),
            dry_run=bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _load_optional_env_mapping(env_file: str | None, *, repo_root: str | Path) -> Mapping[str, str] | None:
    if not env_file:
        return None
    env_file_path = resolve_existing_file(
        env_file,
        label="data operations env file",
        repo_root=repo_root,
        require_repo_outside=True,
    )
    return merged_env_with_file(env_file_path)


def _resolve_news_rss_feed_config_path(
    explicit_path: str | None,
    *,
    env: Mapping[str, str] | None,
    repo_root: str | Path,
) -> Path:
    env_mapping = env if env is not None else os.environ
    selected_path = explicit_path or str(env_mapping.get(NEWS_RSS_FEED_CONFIG_ENV, "")).strip()
    if not selected_path:
        raise ValueError(f"Provide --feed-config or configure {NEWS_RSS_FEED_CONFIG_ENV}.")
    return resolve_existing_file(
        selected_path,
        label="news RSS feed config",
        repo_root=repo_root,
        require_repo_outside=True,
    )


def _handle_paper_safety_bootstrap_config(args: argparse.Namespace, *, stdout: TextIO) -> int:
    env_mapping: Mapping[str, str] | None = None
    if args.env_file:
        env_file_path = resolve_existing_file(
            args.env_file,
            label="data operations env file",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
        env_mapping = merged_env_with_file(env_file_path)
    bootstrap_config = PaperSafetyBootstrapConfig(
        portfolio_name=args.portfolio_name,
        broker_code=args.broker_code,
        account_ref=args.account_ref,
        policy_name=args.policy_name,
        max_single_order_notional=decimal_from_cli(
            args.max_single_order_notional,
            label="max_single_order_notional",
        ),
        max_daily_order_notional=decimal_from_cli(
            args.max_daily_order_notional,
            label="max_daily_order_notional",
        ),
        max_single_order_weight_delta=decimal_from_cli(
            args.max_single_order_weight_delta,
            label="max_single_order_weight_delta",
        ),
        max_post_trade_symbol_weight=decimal_from_cli(
            args.max_post_trade_symbol_weight,
            label="max_post_trade_symbol_weight",
        ),
        min_cash_buffer_weight=decimal_from_cli(
            args.min_cash_buffer_weight,
            label="min_cash_buffer_weight",
        ),
        created_by=args.created_by,
    )

    with _temporary_environ(env_mapping):
        report = run_paper_safety_bootstrap_config(
            config=RuntimeConfig.from_env(),
            bootstrap_config=bootstrap_config,
            dry_run=bool(args.dry_run),
        )
    print_json(report, stdout=stdout, sort_keys=False)
    return 0


def _handle_host_activation_execution_decision(args: argparse.Namespace, *, stdout: TextIO) -> int:
    execution_request_report_path = resolve_existing_file(
        args.execution_request_report,
        label="execution request report",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    decision_record_path = None
    if args.decision_record:
        decision_record_path = resolve_existing_file(
            args.decision_record,
            label="decision record",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
    output_path = None
    if args.output:
        output_path = resolve_output_path(
            args.output,
            label="execution decision output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )

    execution_request_report = load_json_object(
        execution_request_report_path,
        label="execution request report",
    )
    decision_record = (
        load_json_object(decision_record_path, label="decision record") if decision_record_path is not None else None
    )
    report = build_data_operations_live_scheduler_host_activation_execution_decision_report(
        execution_request_report=execution_request_report,
        decision_record=decision_record,
        execution_request_report_path=str(execution_request_report_path),
        decision_record_path=str(decision_record_path) if decision_record_path is not None else "",
    )
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_host_activation_execution_final_preflight(args: argparse.Namespace, *, stdout: TextIO) -> int:
    execution_decision_report_path = resolve_existing_file(
        args.execution_decision_report,
        label="execution decision report",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    env_file_path = resolve_existing_file(
        args.env_file,
        label="data operations env file",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    output_dir = resolve_output_path(
        args.output_dir,
        label="execution final preflight output",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    runtime_readiness_report_path = evidence_dir / "fresh-runtime-env-readiness.json"
    final_preflight_report_path = output_dir / "execution-final-preflight.json"

    execution_decision_report = load_json_object(
        execution_decision_report_path,
        label="execution decision report",
    )
    execution_request_report_path = _resolve_optional_or_recorded_path(
        explicit_path=args.execution_request_report,
        recorded_path=str(execution_decision_report.get("execution_request_report_path", "")),
        label="execution request report",
        repo_root=args.repo_root,
    )
    execution_request_report = load_json_object(
        execution_request_report_path,
        label="execution request report",
    )
    host_activation_plan_report_path = _resolve_optional_or_recorded_path(
        explicit_path=args.host_activation_plan_report,
        recorded_path=str(execution_request_report.get("host_activation_plan_report_path", "")),
        label="host activation plan report",
        repo_root=args.repo_root,
    )
    host_activation_plan_report = load_json_object(
        host_activation_plan_report_path,
        label="host activation plan report",
    )
    runtime_readiness_report = check_data_operations_runtime_env(
        env=merged_env_with_file(env_file_path),
        repo_root=args.repo_root,
        env_file=env_file_path,
        strict=False,
    )
    write_json_report(runtime_readiness_report, output_path=runtime_readiness_report_path, stdout=_NullWriter())

    report = build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
        execution_decision_report=execution_decision_report,
        execution_request_report=execution_request_report,
        host_activation_plan_report=host_activation_plan_report,
        runtime_env_readiness_report=runtime_readiness_report,
        execution_decision_report_path=str(execution_decision_report_path),
        execution_request_report_path=str(execution_request_report_path),
        host_activation_plan_report_path=str(host_activation_plan_report_path),
        runtime_env_readiness_report_path=str(runtime_readiness_report_path),
    )
    write_json_report(report, output_path=final_preflight_report_path, stdout=stdout)
    return 0


def _resolve_optional_or_recorded_path(
    *,
    explicit_path: str | None,
    recorded_path: str,
    label: str,
    repo_root: str | Path,
) -> Path:
    selected_path = explicit_path or recorded_path.strip()
    if not selected_path:
        raise ValueError(f"{label} path is required or must be recorded in upstream evidence.")
    return resolve_existing_file(
        selected_path,
        label=label,
        repo_root=repo_root,
        require_repo_outside=True,
    )


def _handle_host_activation_execution(args: argparse.Namespace, *, stdout: TextIO) -> int:
    execution_final_preflight_report_path = resolve_existing_file(
        args.execution_final_preflight_report,
        label="execution final preflight report",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    confirmation_record_path = None
    if args.confirmation_record:
        confirmation_record_path = resolve_existing_file(
            args.confirmation_record,
            label="host activation execution confirmation record",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
    output_path = None
    if args.output:
        output_path = resolve_output_path(
            args.output,
            label="host activation execution output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )

    execution_final_preflight_report = load_json_object(
        execution_final_preflight_report_path,
        label="execution final preflight report",
    )
    confirmation_record = (
        load_json_object(confirmation_record_path, label="host activation execution confirmation record")
        if confirmation_record_path is not None
        else None
    )
    report = build_data_operations_live_scheduler_host_activation_execution_report(
        execution_final_preflight_report=execution_final_preflight_report,
        confirmation_record=confirmation_record,
        execution_final_preflight_report_path=str(execution_final_preflight_report_path),
        confirmation_record_path=str(confirmation_record_path) if confirmation_record_path is not None else "",
    )
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_manual_host_scheduler_activation_explicit_approval(args: argparse.Namespace, *, stdout: TextIO) -> int:
    host_activation_execution_report_path = resolve_existing_file(
        args.host_activation_execution_report,
        label="host activation execution report",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    approval_record_path = None
    if args.approval_record:
        approval_record_path = resolve_existing_file(
            args.approval_record,
            label="manual host scheduler activation approval record",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )
    output_path = None
    if args.output:
        output_path = resolve_output_path(
            args.output,
            label="manual host scheduler activation approval output",
            repo_root=args.repo_root,
            require_repo_outside=True,
        )

    host_activation_execution_report = load_json_object(
        host_activation_execution_report_path,
        label="host activation execution report",
    )
    approval_record = (
        load_json_object(approval_record_path, label="manual host scheduler activation approval record")
        if approval_record_path is not None
        else None
    )
    report = build_manual_host_scheduler_activation_explicit_approval_report(
        host_activation_execution_report=host_activation_execution_report,
        approval_record=approval_record,
        host_activation_execution_report_path=str(host_activation_execution_report_path),
        approval_record_path=str(approval_record_path) if approval_record_path is not None else "",
    )
    write_json_report(report, output_path=output_path, stdout=stdout)
    return 0


def _handle_manual_host_scheduler_activation_preflight(args: argparse.Namespace, *, stdout: TextIO) -> int:
    manual_approval_report_path = resolve_existing_file(
        args.manual_approval_report,
        label="manual host scheduler activation approval report",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    env_file_path = resolve_existing_file(
        args.env_file,
        label="data operations env file",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    output_dir = resolve_output_path(
        args.output_dir,
        label="manual host scheduler activation preflight output",
        repo_root=args.repo_root,
        require_repo_outside=True,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    runtime_readiness_report_path = evidence_dir / "runtime-env-readiness.json"
    preflight_report_path = output_dir / "manual-host-scheduler-activation-preflight.json"

    manual_approval_report = load_json_object(
        manual_approval_report_path,
        label="manual host scheduler activation approval report",
    )
    runtime_readiness_report = check_data_operations_runtime_env(
        env=merged_env_with_file(env_file_path),
        repo_root=args.repo_root,
        env_file=env_file_path,
        strict=False,
    )
    write_json_report(runtime_readiness_report, output_path=runtime_readiness_report_path, stdout=_NullWriter())
    report = build_manual_host_scheduler_activation_preflight_report(
        manual_approval_report=manual_approval_report,
        runtime_env_readiness_report=runtime_readiness_report,
        manual_approval_report_path=str(manual_approval_report_path),
        runtime_env_readiness_report_path=str(runtime_readiness_report_path),
    )
    write_json_report(report, output_path=preflight_report_path, stdout=stdout)
    return 0


class _NullWriter:
    def write(self, value: str) -> int:
        return len(value)


@contextmanager
def _temporary_environ(env_mapping: Mapping[str, str] | None) -> Iterator[None]:
    if env_mapping is None:
        yield
        return
    previous = os.environ.copy()
    os.environ.clear()
    os.environ.update(env_mapping)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
