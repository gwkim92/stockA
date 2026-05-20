from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

from stockanalysis.ingest.config import ConfigError, RuntimeConfig
from stockanalysis.ingest.http import execute_request
from stockanalysis.ingest.macro.defaults import get_default_series, list_default_series
from stockanalysis.ingest.macro.fred import load_macro_sync_result
from stockanalysis.ingest.macro.models import MacroSeriesSpec
from stockanalysis.ingest.macro.report import load_macro_run_history
from stockanalysis.ingest.macro.sql import render_macro_sync_sql
from stockanalysis.ingest.macro.upsert import (
    resolve_default_macro_specs,
    run_macro_batch_upsert,
    run_macro_upsert,
)
from stockanalysis.ingest.market.backfill import run_market_price_universe_backfill
from stockanalysis.ingest.market.price import run_market_price_batch_upsert, run_market_price_upsert
from stockanalysis.ingest.market.universe import run_market_universe_bootstrap
from stockanalysis.ingest.news.rss import load_news_rss_sync_result
from stockanalysis.ingest.news.chunk_index import (
    DEFAULT_RSS_CHUNK_INDEX_DOCUMENT_LIMIT,
    DEFAULT_RSS_CHUNK_INDEX_EMBEDDING_DIMENSION,
    DEFAULT_RSS_CHUNK_INDEX_MAX_TEXT_CHARS,
    DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME,
    DEFAULT_RSS_CHUNK_INDEX_PROVIDER,
    run_news_rss_local_chunk_index,
)
from stockanalysis.ingest.news.raw_fetch import (
    DEFAULT_NEWS_RSS_RAW_FETCH_LIMIT,
    DEFAULT_NEWS_RSS_RAW_MAX_BODY_BYTES,
    DEFAULT_NEWS_RSS_RAW_USER_AGENT,
    run_news_rss_raw_fetch,
)
from stockanalysis.ingest.news.raw_body_chunk_index import (
    DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_DOCUMENT_LIMIT,
    DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_EMBEDDING_DIMENSION,
    DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_CHUNKS_PER_DOCUMENT,
    DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_TEXT_CHARS,
    DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MODEL_NAME,
    DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_PROVIDER,
    run_news_rss_raw_body_chunk_index,
)
from stockanalysis.ingest.news.upsert import run_news_rss_upsert
from stockanalysis.ingest.portfolio.position import run_position_snapshot_upsert
from stockanalysis.ingest.psql import PsqlExecutionError
from stockanalysis.ingest.registry import get_source, list_sources
from stockanalysis.ingest.sec.classification_impact import run_event_classification_impact_bootstrap
from stockanalysis.ingest.sec.companyfacts import run_sec_companyfacts_upsert
from stockanalysis.ingest.sec.ai_event_extract import run_event_intelligence_llm_extract
from stockanalysis.ingest.sec.event_extract import (
    run_sec_filings_event_batch_extract,
    run_sec_filings_event_extract,
)
from stockanalysis.ingest.sec.instrument_impact import run_event_instrument_impact_bootstrap
from stockanalysis.ingest.sec.raw_fetch import run_sec_filing_raw_fetch
from stockanalysis.ingest.sec.submissions import load_sec_filings_sync_result
from stockanalysis.ingest.sec.upsert import run_sec_filings_upsert
from stockanalysis.operations.artifact_runner import run_data_operation_artifact_command
from stockanalysis.operations.cadence import build_data_operations_cadence_report
from stockanalysis.operations.env_readiness import check_data_operations_runtime_env
from stockanalysis.performance.attribution import run_portfolio_attribution_bootstrap
from stockanalysis.performance.coverage import load_portfolio_outcome_coverage_report
from stockanalysis.performance.outcome import (
    run_performance_outcome_batch_bootstrap,
    run_performance_outcome_bootstrap,
    run_performance_outcome_schedule_bootstrap,
)
from stockanalysis.signal.cycle import run_cycle_state_snapshot
from stockanalysis.signal.features import run_market_feature_snapshot
from stockanalysis.signal.portfolio_remediation_daily import run_portfolio_remediation_daily_automation
from stockanalysis.signal.portfolio_review import run_portfolio_review_bootstrap
from stockanalysis.signal.portfolio_review_report import load_portfolio_review_run_history
from stockanalysis.signal.portfolio_remediation_queue import load_portfolio_remediation_queue
from stockanalysis.signal.portfolio_remediation_ticket import (
    load_portfolio_remediation_ticket_report,
    run_portfolio_remediation_ticket_bootstrap,
    run_portfolio_remediation_ticket_update,
)
from stockanalysis.signal.recommendation import run_recommendation_bootstrap
from stockanalysis.signal.theme_enrichment import run_instrument_theme_enrichment
from stockanalysis.signal.thesis import run_thesis_bootstrap
from stockanalysis.signal.thesis_review import run_thesis_review_bootstrap
from stockanalysis.signal.universe import run_strategy_universe_slice


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stockanalysis-ingest", description="Ingest bootstrap CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-sources", help="List configured source adapters.")

    describe_parser = subparsers.add_parser("describe-source", help="Describe a single source.")
    describe_parser.add_argument("source")

    build_parser_cmd = subparsers.add_parser("build-request", help="Build a request without executing it.")
    _add_source_dataset_args(build_parser_cmd)
    build_parser_cmd.add_argument(
        "--require-credentials",
        action="store_true",
        help="Fail if required env vars are missing instead of showing placeholders.",
    )

    fetch_parser = subparsers.add_parser("fetch", help="Execute a request and print or save the response.")
    _add_source_dataset_args(fetch_parser)
    fetch_parser.add_argument("--output", help="Optional file path to write the response body.")

    subparsers.add_parser("macro-default-series", help="List default FRED macro series bootstrap specs.")

    data_operations_cadence = subparsers.add_parser(
        "data-operations-cadence",
        help="Print the repo-owned data operations cadence registry.",
    )
    data_operations_cadence.add_argument(
        "--cadence",
        choices=("intraday", "daily", "weekly", "monthly"),
        help="Optional cadence filter.",
    )
    data_operations_run = subparsers.add_parser(
        "data-operations-run",
        help="Run a command and capture stdout/stderr/metadata under the data operations artifact root.",
    )
    data_operations_run.add_argument("--job-id", required=True)
    data_operations_run.add_argument(
        "--artifact-root",
        help="Optional artifact root. Defaults to STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT.",
    )
    data_operations_run.add_argument("--timeout-seconds", type=int, default=3600)
    data_operations_run.add_argument(
        "command_argv",
        nargs=argparse.REMAINDER,
        help="Command to run after --.",
    )
    data_operations_env_readiness = subparsers.add_parser(
        "data-operations-env-readiness",
        help="Validate repo-outside data operations runtime env readiness without exposing secrets.",
    )
    data_operations_env_readiness.add_argument(
        "--env-file",
        help="Trusted env file path, used for repo-outside validation and report metadata.",
    )
    data_operations_env_readiness.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Repository root used to reject repo-inside env and artifact paths.",
    )

    macro_sync = subparsers.add_parser(
        "macro-sync",
        help="Build a normalized macro series payload from FRED or local fixtures.",
    )
    _add_macro_series_args(macro_sync)
    macro_sync.add_argument("--sql-output", help="Optional path to write generated SQL upserts.")

    macro_upsert = subparsers.add_parser(
        "macro-upsert",
        help="Fetch or load macro data and upsert it into canonical Postgres through psql.",
    )
    _add_macro_series_args(macro_upsert)

    macro_batch_upsert = subparsers.add_parser(
        "macro-batch-upsert",
        help="Upsert multiple default macro series into canonical Postgres.",
    )
    macro_batch_upsert.add_argument(
        "--series-id",
        action="append",
        default=[],
        help="Repeatable default macro series id. If omitted, all default series are used.",
    )
    macro_batch_upsert.add_argument(
        "--fixtures-dir",
        help="Optional fixture directory containing fred_series_<ID>.json and fred_observations_<ID>.json files.",
    )
    macro_batch_upsert.add_argument("--observation-start")
    macro_batch_upsert.add_argument("--observation-end")

    news_rss_sync = subparsers.add_parser(
        "news-rss-sync",
        help="Parse a free RSS/Atom news feed from a URL or local XML fixture.",
    )
    _add_news_rss_args(news_rss_sync)

    news_rss_upsert = subparsers.add_parser(
        "news-rss-upsert",
        help="Upsert free RSS/Atom news feed items into source_document and event tables.",
    )
    _add_news_rss_args(news_rss_upsert)

    news_rss_local_chunk_index = subparsers.add_parser(
        "news-rss-local-chunk-index",
        help="Create local deterministic document chunks and embedding metadata for RSS source documents.",
    )
    news_rss_local_chunk_index.add_argument("--document-limit", type=int, default=DEFAULT_RSS_CHUNK_INDEX_DOCUMENT_LIMIT)
    news_rss_local_chunk_index.add_argument("--provider", default=DEFAULT_RSS_CHUNK_INDEX_PROVIDER)
    news_rss_local_chunk_index.add_argument("--model-name", default=DEFAULT_RSS_CHUNK_INDEX_MODEL_NAME)
    news_rss_local_chunk_index.add_argument(
        "--embedding-dimension",
        type=int,
        default=DEFAULT_RSS_CHUNK_INDEX_EMBEDDING_DIMENSION,
    )
    news_rss_local_chunk_index.add_argument("--max-text-chars", type=int, default=DEFAULT_RSS_CHUNK_INDEX_MAX_TEXT_CHARS)

    news_rss_raw_fetch = subparsers.add_parser(
        "news-rss-raw-fetch",
        help="Fetch free public RSS article bodies and attach raw artifacts to source_document.",
    )
    news_rss_raw_fetch.add_argument("--limit", type=int, default=DEFAULT_NEWS_RSS_RAW_FETCH_LIMIT)
    news_rss_raw_fetch.add_argument("--external-document-id")
    news_rss_raw_fetch.add_argument(
        "--exclude-url-host",
        action="append",
        default=[],
        help="Repeatable URL host to exclude from raw fetch candidate discovery, such as news.google.com.",
    )
    news_rss_raw_fetch.add_argument(
        "--artifact-root",
        default="artifacts/raw",
        help="Root directory for persisted raw RSS article artifacts.",
    )
    news_rss_raw_fetch.add_argument(
        "--body-file",
        help="Optional local article body fixture. Requires --external-document-id.",
    )
    news_rss_raw_fetch.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing raw_storage_uri instead of discovering only pending documents.",
    )
    news_rss_raw_fetch.add_argument("--max-body-bytes", type=int, default=DEFAULT_NEWS_RSS_RAW_MAX_BODY_BYTES)
    news_rss_raw_fetch.add_argument("--user-agent", default=DEFAULT_NEWS_RSS_RAW_USER_AGENT)

    news_rss_raw_body_chunk_index = subparsers.add_parser(
        "news-rss-raw-body-chunk-index",
        help="Create local deterministic body-text chunks from stored RSS raw HTML artifacts.",
    )
    news_rss_raw_body_chunk_index.add_argument(
        "--document-limit",
        type=int,
        default=DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_DOCUMENT_LIMIT,
    )
    news_rss_raw_body_chunk_index.add_argument("--external-document-id")
    news_rss_raw_body_chunk_index.add_argument(
        "--artifact-root",
        default="artifacts/raw",
        help="Root directory that must contain the file:// raw_storage_uri artifacts.",
    )
    news_rss_raw_body_chunk_index.add_argument(
        "--exclude-url-host",
        action="append",
        default=[],
        help="Repeatable URL host to exclude from raw body chunk candidate discovery, such as news.google.com.",
    )
    news_rss_raw_body_chunk_index.add_argument("--provider", default=DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_PROVIDER)
    news_rss_raw_body_chunk_index.add_argument("--model-name", default=DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MODEL_NAME)
    news_rss_raw_body_chunk_index.add_argument(
        "--embedding-dimension",
        type=int,
        default=DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_EMBEDDING_DIMENSION,
    )
    news_rss_raw_body_chunk_index.add_argument("--max-text-chars", type=int, default=DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_TEXT_CHARS)
    news_rss_raw_body_chunk_index.add_argument(
        "--max-chunks-per-document",
        type=int,
        default=DEFAULT_RSS_RAW_BODY_CHUNK_INDEX_MAX_CHUNKS_PER_DOCUMENT,
    )

    macro_run_history = subparsers.add_parser(
        "macro-run-history",
        help="Report recent macro upsert run history from canonical Postgres.",
    )
    macro_run_history.add_argument("--limit", type=int, default=20)
    macro_run_history.add_argument("--status", help="Optional status filter such as succeeded or failed.")

    market_price_upsert = subparsers.add_parser(
        "market-price-upsert",
        help="Upsert provider daily price bars into canonical Postgres.",
    )
    market_price_upsert.add_argument("--symbol", required=True)
    market_price_upsert.add_argument("--prices-json", help="Optional local provider daily price JSON fixture.")
    market_price_upsert.add_argument("--outputsize", help="Optional provider output size such as compact/full or bar count.")
    market_price_upsert.add_argument(
        "--provider",
        choices=("alpha_vantage", "twelve_data"),
        default="alpha_vantage",
        help="Market price provider. Defaults to alpha_vantage.",
    )

    market_price_batch_upsert = subparsers.add_parser(
        "market-price-batch-upsert",
        help="Upsert multiple provider daily price series into canonical Postgres.",
    )
    market_price_batch_upsert.add_argument("--symbol", action="append", default=[])
    market_price_batch_upsert.add_argument("--fixtures-dir", help="Optional fixture directory for batch mode.")
    market_price_batch_upsert.add_argument("--outputsize", help="Optional provider output size such as compact/full or bar count.")
    market_price_batch_upsert.add_argument(
        "--provider",
        choices=("alpha_vantage", "twelve_data"),
        default="alpha_vantage",
        help="Market price provider. Defaults to alpha_vantage.",
    )
    market_price_batch_upsert.add_argument(
        "--throttle-seconds",
        type=float,
        default=0.0,
        help="Seconds to sleep between provider-backed requests. Fixtures do not sleep.",
    )
    market_price_batch_upsert.add_argument(
        "--max-requests-per-run",
        type=int,
        default=25,
        help="Maximum provider-backed requests in this run. Extra symbols are skipped.",
    )
    market_price_batch_upsert.add_argument(
        "--skip-if-fresh",
        action="store_true",
        help="Skip symbols whose canonical latest daily price date is at or after --freshness-date.",
    )
    market_price_batch_upsert.add_argument(
        "--freshness-date",
        help="Target freshness date in YYYY-MM-DD format. Defaults to the runtime date when --skip-if-fresh is used.",
    )

    market_universe_bootstrap = subparsers.add_parser(
        "market-universe-bootstrap",
        help="Bootstrap a canonical US listed universe from SEC ticker/exchange associations.",
    )
    market_universe_bootstrap.add_argument(
        "--company-tickers-json",
        help="Optional local SEC company_tickers_exchange JSON fixture.",
    )
    market_universe_bootstrap.add_argument(
        "--exchange",
        action="append",
        default=[],
        help="Repeatable supported exchange filter. Defaults to Nasdaq and NYSE.",
    )
    market_universe_bootstrap.add_argument("--limit", type=int, help="Optional maximum number of selected records.")

    market_price_universe_backfill = subparsers.add_parser(
        "market-price-universe-backfill",
        help="Select symbols from canonical universe and run batch daily price backfill.",
    )
    market_price_universe_backfill.add_argument(
        "--exchange",
        action="append",
        default=[],
        help="Repeatable supported exchange filter. Defaults to Nasdaq and NYSE.",
    )
    market_price_universe_backfill.add_argument("--limit", type=int, help="Optional maximum number of selected symbols.")
    market_price_universe_backfill.add_argument("--fixtures-dir", help="Optional fixture directory for batch mode.")
    market_price_universe_backfill.add_argument("--outputsize", help="Optional provider output size such as compact/full or bar count.")
    market_price_universe_backfill.add_argument(
        "--provider",
        choices=("alpha_vantage", "twelve_data"),
        default="alpha_vantage",
        help="Market price provider. Defaults to alpha_vantage.",
    )
    market_price_universe_backfill.add_argument(
        "--throttle-seconds",
        type=float,
        default=0.0,
        help="Seconds to sleep between provider-backed requests. Fixtures do not sleep.",
    )
    market_price_universe_backfill.add_argument(
        "--max-requests-per-run",
        type=int,
        default=25,
        help="Maximum provider-backed requests in this run. Extra symbols are skipped.",
    )
    market_price_universe_backfill.add_argument(
        "--skip-if-fresh",
        action="store_true",
        help="Skip symbols whose canonical latest daily price date is at or after --freshness-date.",
    )
    market_price_universe_backfill.add_argument(
        "--freshness-date",
        help="Target freshness date in YYYY-MM-DD format. Defaults to the runtime date when --skip-if-fresh is used.",
    )

    portfolio_position_snapshot_upsert = subparsers.add_parser(
        "portfolio-position-snapshot-upsert",
        help="Upsert a CSV portfolio position snapshot into canonical Postgres.",
    )
    portfolio_position_snapshot_upsert.add_argument("--positions-csv", required=True)
    portfolio_position_snapshot_upsert.add_argument("--portfolio-name", required=True)
    portfolio_position_snapshot_upsert.add_argument("--snapshot-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    portfolio_position_snapshot_upsert.add_argument("--strategy-name", required=True)
    portfolio_position_snapshot_upsert.add_argument("--base-currency", default="USD")
    portfolio_position_snapshot_upsert.add_argument("--market-code", default="US")
    portfolio_position_snapshot_upsert.add_argument(
        "--live",
        action="store_false",
        dest="is_paper",
        default=True,
        help="Mark portfolio as non-paper. Default is paper.",
    )

    strategy_universe_slice = subparsers.add_parser(
        "strategy-universe-slice",
        help="Create a strategy-specific universe snapshot from canonical instruments and price bars.",
    )
    strategy_universe_slice.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    strategy_universe_slice.add_argument("--strategy-name", required=True)
    strategy_universe_slice.add_argument("--horizon-type", required=True)
    strategy_universe_slice.add_argument("--universe-version", required=True)
    strategy_universe_slice.add_argument("--market-code", default="US")
    strategy_universe_slice.add_argument(
        "--exchange",
        action="append",
        default=[],
        help="Repeatable supported exchange filter. Defaults to Nasdaq and NYSE.",
    )
    strategy_universe_slice.add_argument("--min-observation-count", type=int, default=1)
    strategy_universe_slice.add_argument("--min-adjusted-close", default="0")
    strategy_universe_slice.add_argument("--limit", type=int)

    market_feature_snapshot = subparsers.add_parser(
        "market-feature-snapshot",
        help="Create a deterministic market feature snapshot for a strategy universe batch.",
    )
    market_feature_snapshot.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    market_feature_snapshot.add_argument("--strategy-name", required=True)
    market_feature_snapshot.add_argument("--horizon-type", required=True)
    market_feature_snapshot.add_argument("--universe-version", required=True)
    market_feature_snapshot.add_argument("--market-code", default="US")
    market_feature_snapshot.add_argument("--feature-set-version", default="bootstrap-v1")

    instrument_theme_enrichment = subparsers.add_parser(
        "instrument-theme-enrichment",
        help="Bootstrap internal theme memberships for selected strategy universe instruments.",
    )
    instrument_theme_enrichment.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    instrument_theme_enrichment.add_argument("--strategy-name", required=True)
    instrument_theme_enrichment.add_argument("--horizon-type", required=True)
    instrument_theme_enrichment.add_argument("--universe-version", required=True)
    instrument_theme_enrichment.add_argument("--market-code", default="US")

    cycle_state_snapshot = subparsers.add_parser(
        "cycle-state-snapshot",
        help="Create a deterministic cycle state snapshot for selected internal theme nodes.",
    )
    cycle_state_snapshot.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    cycle_state_snapshot.add_argument("--strategy-name", required=True)
    cycle_state_snapshot.add_argument("--horizon-type", required=True)
    cycle_state_snapshot.add_argument("--universe-version", required=True)
    cycle_state_snapshot.add_argument("--market-code", default="US")
    cycle_state_snapshot.add_argument("--score-version", default="bootstrap-v1")

    recommendation_bootstrap = subparsers.add_parser(
        "recommendation-bootstrap",
        help="Create a deterministic recommendation batch from selected cycle and market evidence.",
    )
    recommendation_bootstrap.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    recommendation_bootstrap.add_argument("--strategy-name", required=True)
    recommendation_bootstrap.add_argument("--horizon-type", required=True)
    recommendation_bootstrap.add_argument("--universe-version", required=True)
    recommendation_bootstrap.add_argument("--market-code", default="US")
    recommendation_bootstrap.add_argument("--score-version", default="bootstrap-v1")

    thesis_bootstrap = subparsers.add_parser(
        "thesis-bootstrap",
        help="Create or update deterministic investment thesis rows for active recommendations.",
    )
    thesis_bootstrap.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    thesis_bootstrap.add_argument("--strategy-name", required=True)
    thesis_bootstrap.add_argument("--horizon-type", required=True)
    thesis_bootstrap.add_argument("--universe-version", required=True)
    thesis_bootstrap.add_argument("--market-code", default="US")
    thesis_bootstrap.add_argument("--thesis-version", default="bootstrap-v1")

    thesis_review_bootstrap = subparsers.add_parser(
        "thesis-review-bootstrap",
        help="Create or update deterministic review rows for active investment thesis.",
    )
    thesis_review_bootstrap.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    thesis_review_bootstrap.add_argument("--strategy-name", required=True)
    thesis_review_bootstrap.add_argument("--horizon-type", required=True)
    thesis_review_bootstrap.add_argument("--universe-version", required=True)
    thesis_review_bootstrap.add_argument("--market-code", default="US")
    thesis_review_bootstrap.add_argument("--review-version", default="bootstrap-v1")
    thesis_review_bootstrap.add_argument("--review-source", default="deterministic_bootstrap")

    portfolio_review_bootstrap = subparsers.add_parser(
        "portfolio-review-bootstrap",
        help="Create or update deterministic portfolio review rows for current position snapshots.",
    )
    portfolio_review_bootstrap.add_argument("--portfolio-name", required=True)
    portfolio_review_bootstrap.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    portfolio_review_bootstrap.add_argument("--strategy-name", required=True)
    portfolio_review_bootstrap.add_argument("--horizon-type", required=True)
    portfolio_review_bootstrap.add_argument("--universe-version", required=True)
    portfolio_review_bootstrap.add_argument("--market-code", default="US")
    portfolio_review_bootstrap.add_argument("--review-version", default="bootstrap-v1")
    portfolio_review_bootstrap.add_argument("--review-source", default="deterministic_bootstrap")
    portfolio_review_bootstrap.add_argument(
        "--coverage-measurement-end-date",
        help="Optional outcome measurement end date in YYYY-MM-DD format for review coverage gating.",
    )

    portfolio_review_run_history = subparsers.add_parser(
        "portfolio-review-run-history",
        help="Report recent portfolio review runs and attention items from canonical Postgres.",
    )
    portfolio_review_run_history.add_argument("--portfolio-name", required=True)
    portfolio_review_run_history.add_argument("--limit", type=int, default=20)
    portfolio_review_run_history.add_argument("--review-source")
    portfolio_review_run_history.add_argument("--risk-level")
    portfolio_review_run_history.add_argument("--action")

    portfolio_remediation_queue = subparsers.add_parser(
        "portfolio-remediation-queue",
        help="Report portfolio review remediation queue items from canonical Postgres.",
    )
    portfolio_remediation_queue.add_argument("--portfolio-name", required=True)
    portfolio_remediation_queue.add_argument("--limit", type=int, default=20)
    portfolio_remediation_queue.add_argument("--review-source")
    portfolio_remediation_queue.add_argument("--action")
    portfolio_remediation_queue.add_argument("--remediation-type")

    portfolio_remediation_ticket_bootstrap = subparsers.add_parser(
        "portfolio-remediation-ticket-bootstrap",
        help="Persist portfolio review remediation queue items as open remediation tickets.",
    )
    portfolio_remediation_ticket_bootstrap.add_argument("--portfolio-name", required=True)
    portfolio_remediation_ticket_bootstrap.add_argument("--limit", type=int, default=20)
    portfolio_remediation_ticket_bootstrap.add_argument("--review-source")
    portfolio_remediation_ticket_bootstrap.add_argument("--action")
    portfolio_remediation_ticket_bootstrap.add_argument("--remediation-type")

    portfolio_remediation_ticket_report = subparsers.add_parser(
        "portfolio-remediation-ticket-report",
        help="Report persisted portfolio remediation tickets from canonical Postgres.",
    )
    portfolio_remediation_ticket_report.add_argument("--portfolio-name", required=True)
    portfolio_remediation_ticket_report.add_argument("--limit", type=int, default=20)
    portfolio_remediation_ticket_report.add_argument(
        "--status",
        default="open",
        help="Ticket status filter. Use 'all' to remove the status filter.",
    )
    portfolio_remediation_ticket_report.add_argument("--action")
    portfolio_remediation_ticket_report.add_argument("--remediation-type")
    portfolio_remediation_ticket_report.add_argument("--suggested-runner")

    portfolio_remediation_ticket_update = subparsers.add_parser(
        "portfolio-remediation-ticket-update",
        help="Update persisted portfolio remediation ticket status.",
    )
    portfolio_remediation_ticket_update.add_argument("--portfolio-name", required=True)
    portfolio_remediation_ticket_update.add_argument("--ticket-id", type=int, required=True)
    portfolio_remediation_ticket_update.add_argument(
        "--status",
        required=True,
        choices=("open", "in_progress", "resolved", "ignored"),
    )

    portfolio_remediation_daily_run = subparsers.add_parser(
        "portfolio-remediation-daily-run",
        help="Run daily portfolio review, remediation ticket bootstrap, and ticket report.",
    )
    portfolio_remediation_daily_run.add_argument("--portfolio-name", required=True)
    portfolio_remediation_daily_run.add_argument("--as-of-date", required=True, help="Snapshot date in YYYY-MM-DD format.")
    portfolio_remediation_daily_run.add_argument("--strategy-name", required=True)
    portfolio_remediation_daily_run.add_argument("--horizon-type", required=True)
    portfolio_remediation_daily_run.add_argument("--universe-version", required=True)
    portfolio_remediation_daily_run.add_argument("--market-code", default="US")
    portfolio_remediation_daily_run.add_argument("--review-version", default="bootstrap-v1")
    portfolio_remediation_daily_run.add_argument("--review-source", default="deterministic_bootstrap")
    portfolio_remediation_daily_run.add_argument(
        "--coverage-measurement-end-date",
        help="Optional outcome measurement end date in YYYY-MM-DD format for review coverage gating.",
    )
    portfolio_remediation_daily_run.add_argument("--ticket-limit", type=int, default=20)
    portfolio_remediation_daily_run.add_argument(
        "--ticket-status",
        default="open",
        choices=("open", "in_progress", "resolved", "ignored", "all"),
        help="Ticket status filter for the final report.",
    )

    performance_outcome_bootstrap = subparsers.add_parser(
        "performance-outcome-bootstrap",
        help="Create or update price-based recommendation and thesis outcome rows.",
    )
    performance_outcome_bootstrap.add_argument("--as-of-date", required=True, help="Recommendation date in YYYY-MM-DD format.")
    performance_outcome_bootstrap.add_argument("--measurement-end-date", required=True, help="Measurement end date in YYYY-MM-DD format.")
    performance_outcome_bootstrap.add_argument("--strategy-name", required=True)
    performance_outcome_bootstrap.add_argument("--horizon-type", required=True)
    performance_outcome_bootstrap.add_argument("--universe-version", required=True)
    performance_outcome_bootstrap.add_argument("--market-code", default="US")
    performance_outcome_bootstrap.add_argument("--outcome-version", default="bootstrap-v1")

    performance_outcome_batch_bootstrap = subparsers.add_parser(
        "performance-outcome-batch-bootstrap",
        help="Create or update price-based outcome rows for multiple measurement dates.",
    )
    performance_outcome_batch_bootstrap.add_argument("--as-of-date", required=True, help="Recommendation date in YYYY-MM-DD format.")
    performance_outcome_batch_bootstrap.add_argument(
        "--measurement-end-date",
        action="append",
        default=[],
        help="Repeatable measurement end date in YYYY-MM-DD format.",
    )
    performance_outcome_batch_bootstrap.add_argument(
        "--horizon-day",
        type=int,
        action="append",
        default=[],
        help="Repeatable calendar-day horizon from --as-of-date.",
    )
    performance_outcome_batch_bootstrap.add_argument("--strategy-name", required=True)
    performance_outcome_batch_bootstrap.add_argument("--horizon-type", required=True)
    performance_outcome_batch_bootstrap.add_argument("--universe-version", required=True)
    performance_outcome_batch_bootstrap.add_argument("--market-code", default="US")
    performance_outcome_batch_bootstrap.add_argument("--outcome-version", default="bootstrap-v1")

    performance_outcome_schedule_bootstrap = subparsers.add_parser(
        "performance-outcome-schedule-bootstrap",
        help="Find due recommendation batch horizons and create missing performance outcome rows.",
    )
    performance_outcome_schedule_bootstrap.add_argument("--due-on-date", required=True, help="Due date in YYYY-MM-DD format.")
    performance_outcome_schedule_bootstrap.add_argument(
        "--horizon-day",
        type=int,
        action="append",
        default=[],
        help="Repeatable calendar-day horizon. Defaults to 30, 90, 180, 365 when omitted.",
    )
    performance_outcome_schedule_bootstrap.add_argument("--market-code")
    performance_outcome_schedule_bootstrap.add_argument("--strategy-name")
    performance_outcome_schedule_bootstrap.add_argument("--horizon-type")
    performance_outcome_schedule_bootstrap.add_argument("--universe-version")
    performance_outcome_schedule_bootstrap.add_argument("--outcome-version", default="bootstrap-v1")
    performance_outcome_schedule_bootstrap.add_argument("--limit", type=int)

    portfolio_attribution_bootstrap = subparsers.add_parser(
        "portfolio-attribution-bootstrap",
        help="Create or update deterministic portfolio attribution rows from position snapshots and thesis outcomes.",
    )
    portfolio_attribution_bootstrap.add_argument("--portfolio-name", required=True)
    portfolio_attribution_bootstrap.add_argument("--snapshot-date", required=True, help="Position snapshot date in YYYY-MM-DD format.")
    portfolio_attribution_bootstrap.add_argument(
        "--measurement-end-date",
        required=True,
        help="Outcome measurement end date in YYYY-MM-DD format.",
    )
    portfolio_attribution_bootstrap.add_argument("--methodology", default="position_weighted_alpha_v1")

    portfolio_outcome_coverage_report = subparsers.add_parser(
        "portfolio-outcome-coverage-report",
        help="Report which portfolio snapshot positions have thesis outcomes for a measurement date.",
    )
    portfolio_outcome_coverage_report.add_argument("--portfolio-name", required=True)
    portfolio_outcome_coverage_report.add_argument("--snapshot-date", required=True, help="Position snapshot date in YYYY-MM-DD format.")
    portfolio_outcome_coverage_report.add_argument(
        "--measurement-end-date",
        required=True,
        help="Outcome measurement end date in YYYY-MM-DD format.",
    )

    sec_filings_sync = subparsers.add_parser(
        "sec-filings-sync",
        help="Normalize SEC submissions payload into filing metadata summary.",
    )
    _add_sec_filings_args(sec_filings_sync)
    sec_filings_sync.add_argument("--sql-output", help="Optional path to write generated SQL upserts.")

    sec_filings_upsert = subparsers.add_parser(
        "sec-filings-upsert",
        help="Upsert SEC filing metadata into canonical Postgres through psql.",
    )
    _add_sec_filings_args(sec_filings_upsert)

    sec_companyfacts_upsert = subparsers.add_parser(
        "sec-companyfacts-upsert",
        help="Upsert selected SEC companyfacts metrics into canonical financial tables through psql.",
    )
    sec_companyfacts_upsert.add_argument("--cik", required=True, help="10-digit filer CIK or raw numeric CIK.")
    sec_companyfacts_upsert.add_argument("--companyfacts-json", help="Optional local SEC companyfacts JSON fixture.")

    sec_filing_raw_fetch = subparsers.add_parser(
        "sec-filing-raw-fetch",
        help="Fetch or load a raw SEC filing body and attach artifact metadata to source_document.",
    )
    sec_filing_raw_fetch.add_argument(
        "--external-document-id",
        required=True,
        help="SEC accession number already present in ingest.source_document.",
    )
    sec_filing_raw_fetch.add_argument(
        "--body-file",
        help="Optional local filing body fixture path. If omitted, fetch from source_document.url.",
    )
    sec_filing_raw_fetch.add_argument(
        "--artifact-root",
        default="artifacts/raw",
        help="Root directory for persisted raw filing artifacts.",
    )
    sec_filing_raw_fetch.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing raw_storage_uri instead of skipping.",
    )

    sec_filings_event_extract = subparsers.add_parser(
        "sec-filings-event-extract",
        help="Extract a heuristic event from a raw SEC filing artifact and upsert event tables.",
    )
    sec_filings_event_extract.add_argument(
        "--external-document-id",
        required=True,
        help="SEC accession number already present in ingest.source_document with raw_storage_uri set.",
    )

    sec_filings_event_batch_extract = subparsers.add_parser(
        "sec-filings-event-batch-extract",
        help="Extract heuristic events for multiple SEC filings with raw artifacts.",
    )
    sec_filings_event_batch_extract.add_argument(
        "--external-document-id",
        action="append",
        default=[],
        help="Repeatable SEC accession number override. If omitted, pending documents are discovered automatically.",
    )
    sec_filings_event_batch_extract.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of pending SEC documents to process when no explicit document ids are supplied.",
    )

    event_intelligence_llm_extract = subparsers.add_parser(
        "event-intelligence-llm-extract",
        help="Persist structured AI-style SEC event extraction metadata and canonical event output.",
    )
    event_intelligence_llm_extract.add_argument(
        "--external-document-id",
        required=True,
        help="SEC accession number already present in ingest.source_document with raw_storage_uri set.",
    )
    event_intelligence_llm_extract.add_argument(
        "--llm-output-json",
        help="Local structured output fixture. Required only when --provider fixture.",
    )
    event_intelligence_llm_extract.add_argument("--provider", default="fixture")
    event_intelligence_llm_extract.add_argument("--model-name", default="gpt-5.4-nano")
    event_intelligence_llm_extract.add_argument("--reasoning-effort", default="low")
    event_intelligence_llm_extract.add_argument("--max-input-chars", type=int, default=8000)
    event_intelligence_llm_extract.add_argument("--min-confidence", type=float, default=0.8)

    event_classification_impact_bootstrap = subparsers.add_parser(
        "event-classification-impact-bootstrap",
        help="Bootstrap minimal classification nodes and link pending SEC events to classification impacts.",
    )
    event_classification_impact_bootstrap.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of pending SEC events to process.",
    )

    event_instrument_impact_bootstrap = subparsers.add_parser(
        "event-instrument-impact-bootstrap",
        help="Bootstrap canonical instrument impacts for pending SEC events.",
    )
    event_instrument_impact_bootstrap.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of pending SEC events to process.",
    )

    return parser


def _add_source_dataset_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source")
    parser.add_argument("dataset")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Repeatable request param override.",
    )


def _add_macro_series_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--series-id", required=True)
    parser.add_argument("--category", help="Required for non-default series ids.")
    parser.add_argument("--region-code", default="US")
    parser.add_argument("--series-json", help="Optional local JSON fixture for FRED /series response.")
    parser.add_argument(
        "--observations-json",
        help="Optional local JSON fixture for FRED /series/observations response.",
    )
    parser.add_argument("--observation-start")
    parser.add_argument("--observation-end")


def _add_sec_filings_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cik", required=True, help="10-digit filer CIK or raw numeric CIK.")
    parser.add_argument("--submissions-json", help="Optional local SEC submissions JSON fixture.")
    parser.add_argument("--max-filings", type=int, help="Optional maximum number of filings to ingest.")


def _add_news_rss_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--feed-name", required=True, help="Stable operator-owned feed name such as wsj-markets.")
    parser.add_argument("--feed-url", required=True, help="Public RSS/Atom feed URL used as source metadata.")
    parser.add_argument("--feed-xml", help="Optional local RSS/Atom XML fixture. If omitted, --feed-url is fetched.")
    parser.add_argument("--limit", type=int, help="Optional maximum number of feed items to process.")
    parser.add_argument("--default-language", default="en", help="Fallback language code when feed items omit language.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = RuntimeConfig.from_env()

    try:
        if args.command == "list-sources":
            _handle_list_sources()
            return 0
        if args.command == "describe-source":
            _handle_describe_source(args.source)
            return 0
        if args.command == "build-request":
            _handle_build_request(
                args.source,
                args.dataset,
                _parse_params(args.param),
                config=config,
                require_credentials=args.require_credentials,
            )
            return 0
        if args.command == "fetch":
            _handle_fetch(
                args.source,
                args.dataset,
                _parse_params(args.param),
                config=config,
                output_path=args.output,
            )
            return 0
        if args.command == "macro-default-series":
            _handle_macro_default_series()
            return 0
        if args.command == "data-operations-cadence":
            _handle_data_operations_cadence(args)
            return 0
        if args.command == "data-operations-run":
            return _handle_data_operations_run(args)
        if args.command == "data-operations-env-readiness":
            _handle_data_operations_env_readiness(args)
            return 0
        if args.command == "macro-sync":
            _handle_macro_sync(args, config=config)
            return 0
        if args.command == "macro-upsert":
            _handle_macro_upsert(args, config=config)
            return 0
        if args.command == "macro-batch-upsert":
            return _handle_macro_batch_upsert(args, config=config)
        if args.command == "news-rss-sync":
            _handle_news_rss_sync(args, config=config)
            return 0
        if args.command == "news-rss-upsert":
            _handle_news_rss_upsert(args, config=config)
            return 0
        if args.command == "news-rss-local-chunk-index":
            _handle_news_rss_local_chunk_index(args, config=config)
            return 0
        if args.command == "news-rss-raw-fetch":
            return _handle_news_rss_raw_fetch(args, config=config)
        if args.command == "news-rss-raw-body-chunk-index":
            return _handle_news_rss_raw_body_chunk_index(args, config=config)
        if args.command == "macro-run-history":
            _handle_macro_run_history(args, config=config)
            return 0
        if args.command == "market-price-upsert":
            _handle_market_price_upsert(args, config=config)
            return 0
        if args.command == "market-price-batch-upsert":
            return _handle_market_price_batch_upsert(args, config=config)
        if args.command == "market-universe-bootstrap":
            _handle_market_universe_bootstrap(args, config=config)
            return 0
        if args.command == "market-price-universe-backfill":
            return _handle_market_price_universe_backfill(args, config=config)
        if args.command == "portfolio-position-snapshot-upsert":
            _handle_portfolio_position_snapshot_upsert(args, config=config)
            return 0
        if args.command == "strategy-universe-slice":
            _handle_strategy_universe_slice(args, config=config)
            return 0
        if args.command == "market-feature-snapshot":
            _handle_market_feature_snapshot(args, config=config)
            return 0
        if args.command == "instrument-theme-enrichment":
            _handle_instrument_theme_enrichment(args, config=config)
            return 0
        if args.command == "cycle-state-snapshot":
            _handle_cycle_state_snapshot(args, config=config)
            return 0
        if args.command == "recommendation-bootstrap":
            _handle_recommendation_bootstrap(args, config=config)
            return 0
        if args.command == "thesis-bootstrap":
            _handle_thesis_bootstrap(args, config=config)
            return 0
        if args.command == "thesis-review-bootstrap":
            _handle_thesis_review_bootstrap(args, config=config)
            return 0
        if args.command == "portfolio-review-bootstrap":
            _handle_portfolio_review_bootstrap(args, config=config)
            return 0
        if args.command == "portfolio-review-run-history":
            _handle_portfolio_review_run_history(args, config=config)
            return 0
        if args.command == "portfolio-remediation-queue":
            _handle_portfolio_remediation_queue(args, config=config)
            return 0
        if args.command == "portfolio-remediation-ticket-bootstrap":
            _handle_portfolio_remediation_ticket_bootstrap(args, config=config)
            return 0
        if args.command == "portfolio-remediation-ticket-report":
            _handle_portfolio_remediation_ticket_report(args, config=config)
            return 0
        if args.command == "portfolio-remediation-ticket-update":
            _handle_portfolio_remediation_ticket_update(args, config=config)
            return 0
        if args.command == "portfolio-remediation-daily-run":
            _handle_portfolio_remediation_daily_run(args, config=config)
            return 0
        if args.command == "performance-outcome-bootstrap":
            _handle_performance_outcome_bootstrap(args, config=config)
            return 0
        if args.command == "performance-outcome-batch-bootstrap":
            _handle_performance_outcome_batch_bootstrap(args, config=config)
            return 0
        if args.command == "performance-outcome-schedule-bootstrap":
            return _handle_performance_outcome_schedule_bootstrap(args, config=config)
        if args.command == "portfolio-attribution-bootstrap":
            _handle_portfolio_attribution_bootstrap(args, config=config)
            return 0
        if args.command == "portfolio-outcome-coverage-report":
            _handle_portfolio_outcome_coverage_report(args, config=config)
            return 0
        if args.command == "sec-filings-sync":
            _handle_sec_filings_sync(args, config=config)
            return 0
        if args.command == "sec-filings-upsert":
            _handle_sec_filings_upsert(args, config=config)
            return 0
        if args.command == "sec-companyfacts-upsert":
            _handle_sec_companyfacts_upsert(args, config=config)
            return 0
        if args.command == "sec-filing-raw-fetch":
            _handle_sec_filing_raw_fetch(args, config=config)
            return 0
        if args.command == "sec-filings-event-extract":
            _handle_sec_filings_event_extract(args, config=config)
            return 0
        if args.command == "sec-filings-event-batch-extract":
            return _handle_sec_filings_event_batch_extract(args, config=config)
        if args.command == "event-intelligence-llm-extract":
            _handle_event_intelligence_llm_extract(args, config=config)
            return 0
        if args.command == "event-classification-impact-bootstrap":
            return _handle_event_classification_impact_bootstrap(args, config=config)
        if args.command == "event-instrument-impact-bootstrap":
            return _handle_event_instrument_impact_bootstrap(args, config=config)
    except (ConfigError, FileNotFoundError, InvalidOperation, KeyError, PsqlExecutionError, ValueError) as exc:
        print(exc)
        return 1

    parser.error("Unknown command")
    return 2


def main_entry() -> None:
    raise SystemExit(main())


def _handle_list_sources() -> None:
    for source in list_sources():
        print(f"{source.name}: {source.description}")


def _handle_data_operations_cadence(args: argparse.Namespace) -> None:
    report = build_data_operations_cadence_report(cadence=args.cadence)
    print(json.dumps(report, indent=2, ensure_ascii=False))


def _handle_data_operations_run(args: argparse.Namespace) -> int:
    command_argv = list(args.command_argv)
    if command_argv and command_argv[0] == "--":
        command_argv = command_argv[1:]
    result = run_data_operation_artifact_command(
        job_id=args.job_id,
        artifact_root=args.artifact_root,
        command_argv=command_argv,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return int(result["exit_code"])


def _handle_data_operations_env_readiness(args: argparse.Namespace) -> None:
    report = check_data_operations_runtime_env(
        repo_root=args.repo_root,
        env_file=args.env_file,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))


def _handle_describe_source(source_name: str) -> None:
    source = get_source(source_name)
    print(json.dumps(source.describe(), indent=2, ensure_ascii=False))


def _handle_build_request(
    source_name: str,
    dataset_name: str,
    params: dict[str, str],
    *,
    config: RuntimeConfig,
    require_credentials: bool,
) -> None:
    source = get_source(source_name)
    request = source.build_request(
        dataset_name,
        params,
        config=config,
        require_credentials=require_credentials,
    )
    print(json.dumps(request.as_dict(), indent=2, ensure_ascii=False))


def _handle_fetch(
    source_name: str,
    dataset_name: str,
    params: dict[str, str],
    *,
    config: RuntimeConfig,
    output_path: str | None,
) -> None:
    source = get_source(source_name)
    request = source.build_request(
        dataset_name,
        params,
        config=config,
        require_credentials=True,
    )
    response = execute_request(request)
    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.body)
        print(
            json.dumps(
                {
                    "status_code": response.status_code,
                    "content_type": response.content_type,
                    "output_path": str(destination),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    payload = {
        "status_code": response.status_code,
        "content_type": response.content_type,
    }
    if response.content_type == "application/json":
        payload["body"] = response.as_json()
    else:
        payload["body_preview"] = response.as_text()[:1000]
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _handle_macro_default_series() -> None:
    payload = [spec.__dict__ for spec in list_default_series()]
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _handle_macro_sync(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    spec = _resolve_macro_series_spec(
        args.series_id,
        category=args.category,
        region_code=args.region_code,
    )
    result = load_macro_sync_result(
        spec,
        config=config,
        series_json_path=args.series_json,
        observations_json_path=args.observations_json,
        observation_start=args.observation_start,
        observation_end=args.observation_end,
    )
    summary = result.summary()
    if args.sql_output:
        destination = Path(args.sql_output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_macro_sync_sql(result), encoding="utf-8")
        summary["sql_output"] = str(destination)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_macro_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    spec = _resolve_macro_series_spec(
        args.series_id,
        category=args.category,
        region_code=args.region_code,
    )
    summary = run_macro_upsert(
        spec,
        config=config,
        series_json_path=args.series_json,
        observations_json_path=args.observations_json,
        observation_start=args.observation_start,
        observation_end=args.observation_end,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_macro_batch_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    specs = resolve_default_macro_specs(args.series_id)
    summary = run_macro_batch_upsert(
        specs,
        config=config,
        fixtures_dir=args.fixtures_dir,
        observation_start=args.observation_start,
        observation_end=args.observation_end,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_series_count"] == 0 else 1


def _handle_news_rss_sync(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    result = load_news_rss_sync_result(
        feed_name=args.feed_name,
        feed_url=args.feed_url,
        config=config,
        feed_xml_path=args.feed_xml,
        limit=args.limit,
        default_language=args.default_language,
    )
    payload = result.summary()
    payload["items"] = [
        {
            "external_document_id": item.external_document_id,
            "title": item.title,
            "url": item.url,
            "published_at": item.published_at.isoformat() if item.published_at else None,
            "language": item.language,
        }
        for item in result.items
    ]
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _handle_news_rss_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_news_rss_upsert(
        feed_name=args.feed_name,
        feed_url=args.feed_url,
        config=config,
        feed_xml_path=args.feed_xml,
        limit=args.limit,
        default_language=args.default_language,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_news_rss_local_chunk_index(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_news_rss_local_chunk_index(
        config=config,
        document_limit=args.document_limit,
        provider=args.provider,
        model_name=args.model_name,
        embedding_dimension=args.embedding_dimension,
        max_text_chars=args.max_text_chars,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_news_rss_raw_fetch(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_news_rss_raw_fetch(
        config=config,
        limit=args.limit,
        external_document_id=args.external_document_id,
        exclude_url_hosts=tuple(args.exclude_url_host),
        artifact_root=args.artifact_root,
        body_path=args.body_file,
        force=args.force,
        max_body_bytes=args.max_body_bytes,
        user_agent=args.user_agent,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_document_count"] == 0 else 1


def _handle_news_rss_raw_body_chunk_index(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_news_rss_raw_body_chunk_index(
        config=config,
        document_limit=args.document_limit,
        external_document_id=args.external_document_id,
        exclude_url_hosts=tuple(args.exclude_url_host),
        artifact_root=args.artifact_root,
        provider=args.provider,
        model_name=args.model_name,
        embedding_dimension=args.embedding_dimension,
        max_text_chars=args.max_text_chars,
        max_chunks_per_document=args.max_chunks_per_document,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_document_count"] == 0 else 1


def _handle_macro_run_history(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = load_macro_run_history(
        config=config,
        limit=args.limit,
        status=args.status,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_market_price_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_market_price_upsert(
        args.symbol,
        config=config,
        prices_json_path=args.prices_json,
        outputsize=args.outputsize,
        provider=args.provider,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_market_price_batch_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_market_price_batch_upsert(
        args.symbol,
        config=config,
        fixtures_dir=args.fixtures_dir,
        outputsize=args.outputsize,
        provider=args.provider,
        throttle_seconds=args.throttle_seconds,
        max_requests_per_run=args.max_requests_per_run,
        skip_if_fresh=args.skip_if_fresh,
        freshness_date=date.fromisoformat(args.freshness_date) if args.freshness_date else None,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_symbol_count"] == 0 else 1


def _handle_market_universe_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_market_universe_bootstrap(
        config=config,
        company_tickers_json_path=args.company_tickers_json,
        exchanges=args.exchange or None,
        limit=args.limit,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_market_price_universe_backfill(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_market_price_universe_backfill(
        config=config,
        exchanges=args.exchange or None,
        limit=args.limit,
        fixtures_dir=args.fixtures_dir,
        outputsize=args.outputsize,
        provider=args.provider,
        throttle_seconds=args.throttle_seconds,
        max_requests_per_run=args.max_requests_per_run,
        skip_if_fresh=args.skip_if_fresh,
        freshness_date=date.fromisoformat(args.freshness_date) if args.freshness_date else None,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_symbol_count"] == 0 else 1


def _handle_portfolio_position_snapshot_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_position_snapshot_upsert(
        config=config,
        positions_csv_path=args.positions_csv,
        portfolio_name=args.portfolio_name,
        snapshot_date=date.fromisoformat(args.snapshot_date),
        strategy_name=args.strategy_name,
        base_currency=args.base_currency,
        market_code=args.market_code,
        is_paper=args.is_paper,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_strategy_universe_slice(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_strategy_universe_slice(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        exchanges=args.exchange or None,
        min_observation_count=args.min_observation_count,
        min_adjusted_close=Decimal(args.min_adjusted_close),
        limit=args.limit,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_market_feature_snapshot(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_market_feature_snapshot(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        feature_set_version=args.feature_set_version,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_instrument_theme_enrichment(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_instrument_theme_enrichment(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_cycle_state_snapshot(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_cycle_state_snapshot(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        score_version=args.score_version,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_recommendation_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_recommendation_bootstrap(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        score_version=args.score_version,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_thesis_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_thesis_bootstrap(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        thesis_version=args.thesis_version,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_thesis_review_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_thesis_review_bootstrap(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        review_version=args.review_version,
        review_source=args.review_source,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_review_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_portfolio_review_bootstrap(
        config=config,
        portfolio_name=args.portfolio_name,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        review_version=args.review_version,
        review_source=args.review_source,
        coverage_measurement_end_date=date.fromisoformat(args.coverage_measurement_end_date)
        if args.coverage_measurement_end_date
        else None,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_review_run_history(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = load_portfolio_review_run_history(
        config=config,
        portfolio_name=args.portfolio_name,
        limit=args.limit,
        review_source=args.review_source,
        risk_level=args.risk_level,
        action=args.action,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_remediation_queue(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = load_portfolio_remediation_queue(
        config=config,
        portfolio_name=args.portfolio_name,
        limit=args.limit,
        review_source=args.review_source,
        action=args.action,
        remediation_type=args.remediation_type,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_remediation_ticket_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_portfolio_remediation_ticket_bootstrap(
        config=config,
        portfolio_name=args.portfolio_name,
        limit=args.limit,
        review_source=args.review_source,
        action=args.action,
        remediation_type=args.remediation_type,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_remediation_ticket_report(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = load_portfolio_remediation_ticket_report(
        config=config,
        portfolio_name=args.portfolio_name,
        limit=args.limit,
        status=args.status,
        action=args.action,
        remediation_type=args.remediation_type,
        suggested_runner=args.suggested_runner,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_remediation_ticket_update(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_portfolio_remediation_ticket_update(
        config=config,
        portfolio_name=args.portfolio_name,
        ticket_id=args.ticket_id,
        status=args.status,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_remediation_daily_run(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_portfolio_remediation_daily_automation(
        config=config,
        portfolio_name=args.portfolio_name,
        as_of_date=date.fromisoformat(args.as_of_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        review_version=args.review_version,
        review_source=args.review_source,
        coverage_measurement_end_date=date.fromisoformat(args.coverage_measurement_end_date)
        if args.coverage_measurement_end_date
        else None,
        ticket_limit=args.ticket_limit,
        ticket_status=args.ticket_status,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_performance_outcome_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_performance_outcome_bootstrap(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        measurement_end_date=date.fromisoformat(args.measurement_end_date),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        outcome_version=args.outcome_version,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_performance_outcome_batch_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_performance_outcome_batch_bootstrap(
        config=config,
        as_of_date=date.fromisoformat(args.as_of_date),
        measurement_end_dates=tuple(date.fromisoformat(value) for value in args.measurement_end_date),
        horizon_days=tuple(args.horizon_day),
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        market_code=args.market_code,
        outcome_version=args.outcome_version,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_performance_outcome_schedule_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_performance_outcome_schedule_bootstrap(
        config=config,
        due_on_date=date.fromisoformat(args.due_on_date),
        horizon_days=tuple(args.horizon_day),
        market_code=args.market_code,
        strategy_name=args.strategy_name,
        horizon_type=args.horizon_type,
        universe_version=args.universe_version,
        outcome_version=args.outcome_version,
        limit=args.limit,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_candidate_count"] == 0 else 1


def _handle_portfolio_attribution_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_portfolio_attribution_bootstrap(
        config=config,
        portfolio_name=args.portfolio_name,
        snapshot_date=date.fromisoformat(args.snapshot_date),
        measurement_end_date=date.fromisoformat(args.measurement_end_date),
        methodology=args.methodology,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_portfolio_outcome_coverage_report(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = load_portfolio_outcome_coverage_report(
        config=config,
        portfolio_name=args.portfolio_name,
        snapshot_date=date.fromisoformat(args.snapshot_date),
        measurement_end_date=date.fromisoformat(args.measurement_end_date),
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_sec_filings_sync(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    result = load_sec_filings_sync_result(
        args.cik,
        config=config,
        submissions_json_path=args.submissions_json,
        max_filings=args.max_filings,
    )
    summary = result.summary()
    if args.sql_output:
        from stockanalysis.ingest.sec.sql import render_sec_filings_upsert_sql

        destination = Path(args.sql_output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_sec_filings_upsert_sql(result), encoding="utf-8")
        summary["sql_output"] = str(destination)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_sec_filings_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_sec_filings_upsert(
        args.cik,
        config=config,
        submissions_json_path=args.submissions_json,
        max_filings=args.max_filings,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_sec_companyfacts_upsert(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_sec_companyfacts_upsert(
        args.cik,
        config=config,
        companyfacts_json_path=args.companyfacts_json,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_sec_filing_raw_fetch(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_sec_filing_raw_fetch(
        args.external_document_id,
        config=config,
        artifact_root=args.artifact_root,
        body_path=args.body_file,
        force=args.force,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_sec_filings_event_extract(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_sec_filings_event_extract(
        args.external_document_id,
        config=config,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_sec_filings_event_batch_extract(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_sec_filings_event_batch_extract(
        config=config,
        external_document_ids=args.external_document_id,
        limit=args.limit,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_document_count"] == 0 else 1


def _handle_event_intelligence_llm_extract(args: argparse.Namespace, *, config: RuntimeConfig) -> None:
    summary = run_event_intelligence_llm_extract(
        args.external_document_id,
        config=config,
        llm_output_json_path=args.llm_output_json,
        provider=args.provider,
        model_name=args.model_name,
        reasoning_effort=args.reasoning_effort,
        max_input_chars=args.max_input_chars,
        min_confidence=args.min_confidence,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def _handle_event_classification_impact_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_event_classification_impact_bootstrap(
        config=config,
        limit=args.limit,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_event_count"] == 0 else 1


def _handle_event_instrument_impact_bootstrap(args: argparse.Namespace, *, config: RuntimeConfig) -> int:
    summary = run_event_instrument_impact_bootstrap(
        config=config,
        limit=args.limit,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["failed_event_count"] == 0 else 1


def _resolve_macro_series_spec(series_id: str, *, category: str | None, region_code: str) -> MacroSeriesSpec:
    default = get_default_series(series_id)
    if default is not None:
        return default
    if not category:
        raise ValueError(f"Unknown default macro series `{series_id}`. Supply --category to continue.")
    return MacroSeriesSpec(series_id=series_id.upper(), category=category, region_code=region_code)


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for item in values:
        if "=" not in item:
            raise ValueError(f"Invalid --param value `{item}`. Expected KEY=VALUE.")
        key, value = item.split("=", 1)
        params[key] = value
    return params


if __name__ == "__main__":
    raise SystemExit(main())
