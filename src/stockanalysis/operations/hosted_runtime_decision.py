from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Mapping


FORBIDDEN_HOSTED_RUNTIME_TOKENS = (
    "postgresql://",
    "api-key=",
    "api_key=",
    "bearer ",
    "password=",
    "sk-",
)
HOSTED_RUNTIME_REFERENCES = (
    {
        "label": "Supabase pricing",
        "url": "https://supabase.com/pricing",
        "claim": "Free plan includes a dedicated Postgres database with a 500 MB database size limit.",
    },
    {
        "label": "Supabase billing",
        "url": "https://supabase.com/docs/guides/platform/billing-on-supabase",
        "claim": "Free plan allows two active free projects, subject to project limits and pausing behavior.",
    },
    {
        "label": "Supabase database size",
        "url": "https://supabase.com/docs/guides/platform/database-size",
        "claim": "Free plan projects enter read-only mode when database size exceeds 500 MB.",
    },
    {
        "label": "Render free Postgres",
        "url": "https://render.com/free",
        "claim": "Free Render Postgres databases expire after 30 days.",
    },
    {
        "label": "GitHub Actions billing",
        "url": "https://docs.github.com/actions/administering-github-actions/usage-limits-billing-and-administration",
        "claim": "Standard GitHub-hosted runners are free for public repositories.",
    },
)


def build_hosted_database_runtime_decision(
    *,
    repo_visibility: str = "public",
    zero_budget_required: bool = True,
    hosted_database_configured: bool = False,
    existing_runtime_host_available: bool = False,
    supabase_free_project_available: bool = True,
    local_only_accepted: bool = False,
    github_actions_allowed: bool = True,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    visibility = _normalize_repo_visibility(repo_visibility)
    candidates = _candidate_matrix(
        repo_visibility=visibility,
        zero_budget_required=zero_budget_required,
        hosted_database_configured=hosted_database_configured,
        existing_runtime_host_available=existing_runtime_host_available,
        supabase_free_project_available=supabase_free_project_available,
        local_only_accepted=local_only_accepted,
        github_actions_allowed=github_actions_allowed,
    )
    decision = _select_decision(
        hosted_database_configured=hosted_database_configured,
        existing_runtime_host_available=existing_runtime_host_available,
        supabase_free_project_available=supabase_free_project_available,
        local_only_accepted=local_only_accepted,
        github_actions_allowed=github_actions_allowed,
        repo_visibility=visibility,
    )
    generated_at_value = _coerce_utc(generated_at or datetime.now(timezone.utc))
    report = {
        "report_name": "hosted_database_runtime_decision",
        "generated_at": _format_timestamp(generated_at_value),
        "repo_visibility": visibility,
        "zero_budget_required": zero_budget_required,
        "hosted_database_configured": hosted_database_configured,
        "existing_runtime_host_available": existing_runtime_host_available,
        "supabase_free_project_available": supabase_free_project_available,
        "local_only_accepted": local_only_accepted,
        "github_actions_allowed": github_actions_allowed,
        "provisioning_performed": False,
        "database_created": False,
        "secret_written": False,
        "workflow_file_created": False,
        "scheduler_deployed": False,
        "recommended_path": decision["recommended_path"],
        "decision_status": decision["decision_status"],
        "blocking_reasons": decision["blocking_reasons"],
        "required_next_step": decision["required_next_step"],
        "manual_next_step": decision["manual_next_step"],
        "candidate_matrix": candidates,
        "operator_setup_requirements": decision["operator_setup_requirements"],
        "secrets_policy": "metadata_only_no_database_url_or_provider_secret",
        "references": list(HOSTED_RUNTIME_REFERENCES),
    }
    _assert_secret_free(report)
    return report


def render_hosted_database_runtime_decision_markdown(report: Mapping[str, object]) -> str:
    _assert_secret_free(report)
    lines = [
        "# Hosted Database Runtime Decision",
        "",
        f"- decision status: `{report.get('decision_status', '')}`",
        f"- recommended path: `{report.get('recommended_path', '')}`",
        f"- hosted database configured: `{str(report.get('hosted_database_configured')).lower()}`",
        f"- existing runtime host available: `{str(report.get('existing_runtime_host_available')).lower()}`",
        f"- provisioning performed: `{str(report.get('provisioning_performed')).lower()}`",
        "",
        "## Blocking Reasons",
    ]
    blocking_reasons = report.get("blocking_reasons", [])
    if isinstance(blocking_reasons, list) and blocking_reasons:
        for reason in blocking_reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- none")

    lines.extend(["", "## Candidate Matrix"])
    candidates = report.get("candidate_matrix", [])
    if isinstance(candidates, list):
        for candidate in candidates:
            if isinstance(candidate, Mapping):
                lines.append(
                    "- "
                    f"{candidate.get('target', '')}: "
                    f"{candidate.get('status', '')}; "
                    f"{candidate.get('reason', '')}"
                )

    lines.extend(
        [
            "",
            "## Boundary",
            "- This decision does not create a database.",
            "- It does not write secrets or GitHub Actions workflow files.",
            "- It does not run migrations, scheduler jobs, or hosted worker smoke.",
            "",
        ]
    )
    return "\n".join(lines)


def _candidate_matrix(
    *,
    repo_visibility: str,
    zero_budget_required: bool,
    hosted_database_configured: bool,
    existing_runtime_host_available: bool,
    supabase_free_project_available: bool,
    local_only_accepted: bool,
    github_actions_allowed: bool,
) -> list[dict[str, object]]:
    public_actions_free = repo_visibility == "public" and github_actions_allowed
    return [
        {
            "target": "supabase_free_postgres_plus_github_actions_worker",
            "zero_budget_fit": zero_budget_required and supabase_free_project_available and public_actions_free,
            "current_ready": hosted_database_configured and public_actions_free,
            "external_scheduler_ready": hosted_database_configured and public_actions_free,
            "status": "ready_for_migration_smoke" if hosted_database_configured else "setup_required",
            "reason": (
                "Best no-server path for this public repo once the user creates the Supabase project and stores secrets."
                if supabase_free_project_available
                else "Supabase free project capacity is not available."
            ),
            "requires": [
                "supabase_free_project",
                "database_connection_string_in_repo_outside_env",
                "github_actions_repository_secret",
                "migration_and_seed_smoke",
            ],
            "limits": [
                "500MB_database_size",
                "free_project_pause_after_inactivity",
                "no_production_grade_backup_on_free_plan",
            ],
        },
        {
            "target": "existing_host_postgres_plus_systemd_worker",
            "zero_budget_fit": zero_budget_required and existing_runtime_host_available,
            "current_ready": existing_runtime_host_available,
            "external_scheduler_ready": existing_runtime_host_available,
            "status": "ready_for_host_runtime_smoke" if existing_runtime_host_available else "blocked",
            "reason": (
                "Best if the user already owns a VPS/NAS/server that can host Postgres and systemd."
                if existing_runtime_host_available
                else "No existing always-on host has been provided."
            ),
            "requires": [
                "existing_always_on_host",
                "postgres_instance",
                "repo_checkout",
                "repo_outside_runtime_env",
            ],
            "limits": ["operator_managed_backups", "operator_managed_security_updates"],
        },
        {
            "target": "render_free_postgres",
            "zero_budget_fit": True,
            "current_ready": False,
            "external_scheduler_ready": False,
            "status": "rejected",
            "reason": "Rejected for durable project state because Free Render Postgres expires after 30 days.",
            "requires": ["provider_account"],
            "limits": ["30_day_database_expiry", "not_suitable_for_continuous_investment_history"],
        },
        {
            "target": "local_only_postgres_plus_local_worker",
            "zero_budget_fit": True,
            "current_ready": local_only_accepted,
            "external_scheduler_ready": False,
            "status": "local_only_ready" if local_only_accepted else "available_but_not_external",
            "reason": (
                "Can keep using the current local MVP, but collection stops when the Mac is off."
                if local_only_accepted
                else "Available immediately, but does not satisfy server-side scheduler goal."
            ),
            "requires": ["mac_is_on", "local_postgres", "local_runtime_env"],
            "limits": ["not_external_scheduler_ready", "operator_machine_dependency"],
        },
    ]


def _select_decision(
    *,
    hosted_database_configured: bool,
    existing_runtime_host_available: bool,
    supabase_free_project_available: bool,
    local_only_accepted: bool,
    github_actions_allowed: bool,
    repo_visibility: str,
) -> dict[str, object]:
    if existing_runtime_host_available:
        return {
            "recommended_path": "existing_host_postgres_plus_systemd_worker",
            "decision_status": "ready_for_existing_host_runtime_smoke",
            "blocking_reasons": [],
            "required_next_step": "existing-host-runtime-smoke",
            "manual_next_step": "existing-host-runtime-smoke",
            "operator_setup_requirements": [
                "confirm_host_access",
                "prepare_repo_outside_env",
                "run_migration_seed_smoke",
            ],
        }
    if hosted_database_configured and github_actions_allowed and repo_visibility == "public":
        return {
            "recommended_path": "supabase_free_postgres_plus_github_actions_worker",
            "decision_status": "ready_for_hosted_database_migration_smoke",
            "blocking_reasons": [],
            "required_next_step": "supabase-hosted-db-migration-smoke",
            "manual_next_step": "supabase-hosted-db-migration-smoke",
            "operator_setup_requirements": [
                "confirm_repo_outside_database_url",
                "run_migrations_against_hosted_db",
                "run_read_only_fastapi_against_hosted_db",
                "prepare_github_actions_secret_packet",
            ],
        }
    if local_only_accepted:
        return {
            "recommended_path": "local_only_postgres_plus_local_worker",
            "decision_status": "local_only_runtime_selected",
            "blocking_reasons": ["external_scheduler_not_enabled_by_choice"],
            "required_next_step": "local-only-worker-hardening",
            "manual_next_step": "local-only-worker-hardening",
            "operator_setup_requirements": [
                "keep_mac_awake_or_accept_collection_gaps",
                "keep_repo_outside_env_current",
                "review_local_worker_data_health",
            ],
        }
    if not supabase_free_project_available:
        return {
            "recommended_path": "blocked_no_free_hosted_database_capacity",
            "decision_status": "blocked_no_free_hosted_database_capacity",
            "blocking_reasons": ["no_free_hosted_database_candidate_confirmed"],
            "required_next_step": "free-hosted-database-provider-research",
            "manual_next_step": "free-hosted-database-provider-research",
            "operator_setup_requirements": ["find_confirmed_free_postgres_provider_or_accept_local_only"],
        }
    return {
        "recommended_path": "supabase_free_postgres_plus_github_actions_worker",
        "decision_status": "setup_required_for_hosted_database",
        "blocking_reasons": [
            "hosted_database_not_configured",
            "database_connection_secret_not_provided",
            "hosted_database_migration_smoke_not_run",
        ],
        "required_next_step": "supabase-free-postgres-setup-packet",
        "manual_next_step": "supabase-free-postgres-setup-packet",
        "operator_setup_requirements": [
            "create_supabase_free_project",
            "copy_database_connection_string_to_repo_outside_env",
            "prepare_github_actions_repository_secret_names",
            "run_hosted_db_migration_seed_smoke_before_scheduler",
        ],
    }


def _normalize_repo_visibility(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in {"public", "private"}:
        raise ValueError("repo_visibility must be public or private.")
    return normalized


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    return _coerce_utc(value).isoformat().replace("+00:00", "Z")


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_HOSTED_RUNTIME_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("hosted runtime decision payload contains secret-like value.")
