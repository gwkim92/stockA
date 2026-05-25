from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Literal

from stockanalysis.ingest.macro.sql import sql_literal


Cadence = Literal["intraday", "daily", "weekly", "monthly"]

DATA_OPERATIONS_TIMEZONE = "America/New_York"
DATA_OPERATIONS_ARTIFACT_ROOT_ENV = "STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT"


@dataclass(frozen=True)
class DataOperationCadence:
    job_id: str
    pipeline_name: str
    domain: str
    cadence: Cadence
    command_template: str
    expected_after_local: str
    stale_after_hours: int
    artifact_policy: str
    required_env_groups: tuple[str, ...]
    data_health_dataset: str | None = None

    def as_payload(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "pipeline_name": self.pipeline_name,
            "domain": self.domain,
            "cadence": self.cadence,
            "timezone": DATA_OPERATIONS_TIMEZONE,
            "command_template": self.command_template,
            "expected_after_local": self.expected_after_local,
            "stale_after_hours": self.stale_after_hours,
            "artifact_policy": self.artifact_policy,
            "artifact_root_env": DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
            "required_env_groups": list(self.required_env_groups),
            "data_health_dataset": self.data_health_dataset,
        }


DATA_OPERATION_CADENCES: tuple[DataOperationCadence, ...] = (
    DataOperationCadence(
        job_id="market-universe-weekly",
        pipeline_name="market_universe_bootstrap",
        domain="market",
        cadence="weekly",
        command_template="stockanalysis-ingest market-universe-bootstrap --exchange Nasdaq --exchange NYSE",
        expected_after_local="07:00 Monday",
        stale_after_hours=216,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "sec_identity"),
        data_health_dataset="ref.instrument",
    ),
    DataOperationCadence(
        job_id="market-price-daily",
        pipeline_name="market_price_upsert",
        domain="market",
        cadence="daily",
        command_template=(
            "stockanalysis-operations market-price-daily-run "
            "--skip-if-fresh"
        ),
        expected_after_local="18:30",
        stale_after_hours=36,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "market_price_provider"),
        data_health_dataset="market.daily_price_bar",
    ),
    DataOperationCadence(
        job_id="portfolio-position-daily",
        pipeline_name="portfolio_position_snapshot_upsert",
        domain="portfolio",
        cadence="daily",
        command_template="stockanalysis-ingest portfolio-position-snapshot-upsert --positions-csv <CSV> ...",
        expected_after_local="18:45",
        stale_after_hours=36,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "portfolio_snapshot_source"),
        data_health_dataset="portfolio.position_snapshot",
    ),
    DataOperationCadence(
        job_id="portfolio-remediation-daily",
        pipeline_name="portfolio_remediation_daily_automation",
        domain="portfolio",
        cadence="daily",
        command_template="stockanalysis-ingest portfolio-remediation-daily-run --as-of-date <YYYY-MM-DD> ...",
        expected_after_local="19:00",
        stale_after_hours=36,
        artifact_policy="stdout_json_stderr_log_and_summary_link",
        required_env_groups=("database",),
    ),
    DataOperationCadence(
        job_id="macro-weekly",
        pipeline_name="macro_upsert",
        domain="macro",
        cadence="weekly",
        command_template="stockanalysis-ingest macro-batch-upsert --series-id <SERIES>...",
        expected_after_local="07:30 Monday",
        stale_after_hours=192,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "fred"),
        data_health_dataset="macro.observation",
    ),
    DataOperationCadence(
        job_id="news-rss-daily",
        pipeline_name="news_rss_upsert",
        domain="news",
        cadence="intraday",
        command_template="stockanalysis-operations news-rss-daily-run --env-file <ENV>",
        expected_after_local="09:00",
        stale_after_hours=4,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "news_rss_feed_config"),
        data_health_dataset="ingest.source_document",
    ),
    DataOperationCadence(
        job_id="news-missing-instrument-bootstrap-intraday",
        pipeline_name="news_missing_instrument_bootstrap",
        domain="news",
        cadence="intraday",
        command_template="stockanalysis-operations news-missing-instrument-bootstrap-run --env-file <ENV>",
        expected_after_local="09:03",
        stale_after_hours=4,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "sec_identity"),
        data_health_dataset="ref.instrument",
    ),
    DataOperationCadence(
        job_id="news-rss-enrichment-intraday",
        pipeline_name="news_rss_event_enrichment",
        domain="news",
        cadence="intraday",
        command_template="stockanalysis-operations news-rss-enrich-run --env-file <ENV>",
        expected_after_local="09:05",
        stale_after_hours=4,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database",),
        data_health_dataset="event.event",
    ),
    DataOperationCadence(
        job_id="news-korean-translation-intraday",
        pipeline_name="news_rss_korean_translation",
        domain="ai",
        cadence="intraday",
        command_template="stockanalysis-operations news-rss-translation-run --env-file <ENV> --provider codex_oauth --execute",
        expected_after_local="09:07",
        stale_after_hours=4,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database", "openai_or_llm_provider"),
        data_health_dataset="ingest.source_document",
    ),
    DataOperationCadence(
        job_id="sec-filings-weekly",
        pipeline_name="sec_filings_upsert",
        domain="sec",
        cadence="weekly",
        command_template="stockanalysis-ingest sec-filings-upsert --cik <CIK>...",
        expected_after_local="08:00 Monday",
        stale_after_hours=192,
        artifact_policy="stdout_json_stderr_log_and_raw_artifacts",
        required_env_groups=("database", "sec_identity"),
        data_health_dataset="ingest.source_document",
    ),
    DataOperationCadence(
        job_id="sec-companyfacts-weekly",
        pipeline_name="sec_companyfacts_upsert",
        domain="sec",
        cadence="weekly",
        command_template="stockanalysis-ingest sec-companyfacts-upsert --cik <CIK>",
        expected_after_local="08:20 Monday",
        stale_after_hours=216,
        artifact_policy="stdout_json_stderr_log_and_financial_fact_counts",
        required_env_groups=("database", "sec_identity"),
        data_health_dataset="market.financial_statement_period",
    ),
    DataOperationCadence(
        job_id="financial-metric-normalization-weekly",
        pipeline_name="financial_metric_normalization",
        domain="fundamentals",
        cadence="weekly",
        command_template="stockanalysis-operations financial-metric-normalization-run --env-file <ENV> --as-of-date <YYYY-MM-DD> --execute",
        expected_after_local="08:30 Monday",
        stale_after_hours=216,
        artifact_policy="stdout_json_stderr_log_and_metric_counts",
        required_env_groups=("database",),
        data_health_dataset="market.financial_metric_normalized",
    ),
    DataOperationCadence(
        job_id="peer-relative-analysis-weekly",
        pipeline_name="peer_relative_analysis",
        domain="fundamentals",
        cadence="weekly",
        command_template="stockanalysis-operations peer-relative-analysis-run --env-file <ENV> --as-of-date <YYYY-MM-DD> --execute",
        expected_after_local="08:40 Monday",
        stale_after_hours=216,
        artifact_policy="stdout_json_stderr_log_and_peer_counts",
        required_env_groups=("database",),
        data_health_dataset="market.peer_relative_snapshot",
    ),
    DataOperationCadence(
        job_id="valuation-snapshot-weekly",
        pipeline_name="valuation_snapshot",
        domain="fundamentals",
        cadence="weekly",
        command_template="stockanalysis-operations valuation-snapshot-run --env-file <ENV> --as-of-date <YYYY-MM-DD> --execute",
        expected_after_local="08:50 Monday",
        stale_after_hours=216,
        artifact_policy="stdout_json_stderr_log_and_valuation_counts",
        required_env_groups=("database",),
        data_health_dataset="market.valuation_snapshot",
    ),
    DataOperationCadence(
        job_id="event-intelligence-weekly",
        pipeline_name="event_intelligence_llm_extract",
        domain="ai",
        cadence="intraday",
        command_template="stockanalysis-operations operating-data-run --data-operations-env-file <ENV> --profile news-intraday --execute",
        expected_after_local="09:10",
        stale_after_hours=4,
        artifact_policy="stdout_json_stderr_log_and_ai_artifact_id",
        required_env_groups=("database", "news_rss_feed_config", "openai_or_llm_provider"),
        data_health_dataset="ai.extraction_artifact",
    ),
    DataOperationCadence(
        job_id="cycle-recommendation-weekly",
        pipeline_name="cycle_state_snapshot",
        domain="signal",
        cadence="weekly",
        command_template="stockanalysis-ingest cycle-state-snapshot --as-of-date <YYYY-MM-DD> ...",
        expected_after_local="10:00 Monday",
        stale_after_hours=216,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database",),
        data_health_dataset="signal.cycle_state_snapshot",
    ),
    DataOperationCadence(
        job_id="cycle-community-ai-summary-daily",
        pipeline_name="cycle_community_ai_summary",
        domain="ai",
        cadence="daily",
        command_template="stockanalysis-operations cycle-community-ai-summary-v2-run --env-file <ENV> --provider codex_oauth --execute",
        expected_after_local="19:20",
        stale_after_hours=36,
        artifact_policy="stdout_json_stderr_log_and_model_invocation_id",
        required_env_groups=("database", "openai_or_llm_provider"),
        data_health_dataset="ai.cycle_community_summary",
    ),
    DataOperationCadence(
        job_id="recommendation-outcome-backfill-daily",
        pipeline_name="performance_outcome_schedule_bootstrap",
        domain="performance",
        cadence="daily",
        command_template="stockanalysis-operations recommendation-outcome-backfill-run --env-file <ENV> --due-on-date <YYYY-MM-DD> --horizon-day 30 --execute",
        expected_after_local="19:30",
        stale_after_hours=36,
        artifact_policy="stdout_json_stderr_log_and_backfill_summary",
        required_env_groups=("database", "market_price_history"),
        data_health_dataset="performance.recommendation_outcome",
    ),
    DataOperationCadence(
        job_id="recommendation-quality-eval-daily",
        pipeline_name="recommendation_quality_eval",
        domain="performance",
        cadence="daily",
        command_template="stockanalysis-operations recommendation-quality-eval-run --env-file <ENV> --horizon 30d --execute",
        expected_after_local="19:40",
        stale_after_hours=36,
        artifact_policy="stdout_json_stderr_log_and_eval_run_id",
        required_env_groups=("database",),
        data_health_dataset="ai.eval_run",
    ),
    DataOperationCadence(
        job_id="performance-outcome-monthly",
        pipeline_name="performance_outcome_schedule_bootstrap",
        domain="performance",
        cadence="monthly",
        command_template="stockanalysis-operations recommendation-outcome-backfill-run --env-file <ENV> --due-on-date <YYYY-MM-DD> --execute",
        expected_after_local="09:00 first-business-day",
        stale_after_hours=840,
        artifact_policy="stdout_json_stderr_log_and_failure_candidates",
        required_env_groups=("database", "market_price_history"),
        data_health_dataset="performance.thesis_outcome",
    ),
    DataOperationCadence(
        job_id="portfolio-attribution-monthly",
        pipeline_name="portfolio_attribution_bootstrap",
        domain="performance",
        cadence="monthly",
        command_template="stockanalysis-ingest portfolio-attribution-bootstrap --snapshot-date <YYYY-MM-DD> ...",
        expected_after_local="10:00 first-business-day",
        stale_after_hours=840,
        artifact_policy="stdout_json_and_stderr_log",
        required_env_groups=("database",),
        data_health_dataset="performance.portfolio_attribution",
    ),
)


def list_data_operation_cadences(*, cadence: Cadence | None = None) -> tuple[DataOperationCadence, ...]:
    if cadence is None:
        return DATA_OPERATION_CADENCES
    return tuple(job for job in DATA_OPERATION_CADENCES if job.cadence == cadence)


def get_data_operation_cadence(job_id: str) -> DataOperationCadence:
    for job in DATA_OPERATION_CADENCES:
        if job.job_id == job_id:
            return job
    raise ValueError(f"Unknown data operation job_id `{job_id}`.")


def build_data_operations_cadence_report(
    *,
    cadence: Cadence | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    jobs = list_data_operation_cadences(cadence=cadence)
    cadence_counts = Counter(job.cadence for job in jobs)
    generated_at_value = generated_at or datetime.now(timezone.utc)

    return {
        "report_name": "data_operations_cadence_foundation",
        "generated_at": _format_generated_at(generated_at_value),
        "timezone": DATA_OPERATIONS_TIMEZONE,
        "artifact_root_env": DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
        "activation_status": "reference_only_not_scheduled",
        "cadence_filter": cadence or "all",
        "cadence_counts": dict(sorted(cadence_counts.items())),
        "job_count": len(jobs),
        "jobs": [job.as_payload() for job in jobs],
        "guardrails": [
            "secrets remain outside the repository",
            "real scheduler activation requires a separate task contract",
            "stdout/stderr artifacts must be stored under the operator-provided artifact root",
            "data-health reads latest ops.pipeline_run state and does not mutate data",
        ],
    }


def render_data_operations_expected_jobs_sql_values(jobs: Iterable[DataOperationCadence] | None = None) -> str:
    selected_jobs = tuple(jobs) if jobs is not None else DATA_OPERATION_CADENCES
    return ",\n        ".join(_render_expected_job_tuple(job) for job in selected_jobs)


def _render_expected_job_tuple(job: DataOperationCadence) -> str:
    return (
        "("
        f"{sql_literal(job.pipeline_name)}, "
        f"{sql_literal(job.job_id)}, "
        f"{sql_literal(job.domain)}, "
        f"{sql_literal(job.cadence)}, "
        f"{sql_literal(job.expected_after_local)}, "
        f"{job.stale_after_hours}, "
        f"{sql_literal(job.artifact_policy)}"
        ")"
    )


def _format_generated_at(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
