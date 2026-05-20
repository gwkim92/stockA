from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Mapping


SCHEDULER_DEPLOYMENT_TARGETS = (
    "github_actions_scheduled_workflow",
    "vps_systemd_timer",
    "kubernetes_cronjob",
    "managed_scheduler",
    "local_host_scheduler",
)
DEFAULT_DECISION_REFERENCES = (
    {
        "label": "GitHub Actions billing and usage",
        "url": "https://docs.github.com/actions/administering-github-actions/usage-limits-billing-and-administration",
        "claim": "Standard GitHub-hosted runners are free for public repositories.",
    },
    {
        "label": "GitHub Actions schedule event",
        "url": "https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows",
        "claim": "Scheduled workflows use UTC POSIX cron syntax and the shortest interval is 5 minutes.",
    },
    {
        "label": "GitHub Actions secrets",
        "url": "https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/using-secrets-in-github-actions",
        "claim": "Repository secrets can be injected into workflows without committing secret values.",
    },
)
FORBIDDEN_DEPLOYMENT_DECISION_TOKENS = (
    "postgresql://",
    "api-key=",
    "api_key=",
    "bearer ",
    "password=",
    "sk-",
)


def build_server_scheduler_deployment_target_decision(
    *,
    repo_visibility: str = "public",
    zero_budget_required: bool = True,
    hosted_database_configured: bool = False,
    runtime_host_available: bool = False,
    mac_host_scheduler_allowed: bool = False,
    kubernetes_cluster_available: bool = False,
    managed_scheduler_free_tier_confirmed: bool = False,
    github_actions_allowed: bool = True,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    visibility = _normalize_repo_visibility(repo_visibility)
    generated_at_value = _coerce_utc(generated_at or datetime.now(timezone.utc))
    candidates = _build_candidate_matrix(
        repo_visibility=visibility,
        zero_budget_required=zero_budget_required,
        hosted_database_configured=hosted_database_configured,
        runtime_host_available=runtime_host_available,
        mac_host_scheduler_allowed=mac_host_scheduler_allowed,
        kubernetes_cluster_available=kubernetes_cluster_available,
        managed_scheduler_free_tier_confirmed=managed_scheduler_free_tier_confirmed,
        github_actions_allowed=github_actions_allowed,
    )
    decision = _select_decision(candidates)
    report = {
        "report_name": "server_scheduler_deployment_target_decision",
        "generated_at": _format_timestamp(generated_at_value),
        "repo_visibility": visibility,
        "zero_budget_required": zero_budget_required,
        "hosted_database_configured": hosted_database_configured,
        "runtime_host_available": runtime_host_available,
        "mac_host_scheduler_allowed": mac_host_scheduler_allowed,
        "kubernetes_cluster_available": kubernetes_cluster_available,
        "managed_scheduler_free_tier_confirmed": managed_scheduler_free_tier_confirmed,
        "github_actions_allowed": github_actions_allowed,
        "scheduler_deployed": False,
        "scheduler_deployment_allowed_in_this_task": False,
        "host_mutation_allowed": False,
        "launchctl_executed": False,
        "workflow_file_created": False,
        "recommended_target": decision["recommended_target"],
        "decision_status": decision["decision_status"],
        "blocking_reasons": decision["blocking_reasons"],
        "candidate_matrix": candidates,
        "why_not_web_server_scheduler": [
            "FastAPI and Next.js request servers can be scaled to multiple instances, causing duplicate scheduled runs.",
            "Long ingest and AI evidence jobs conflict with request lifecycle, deploy restarts, and timeouts.",
            "Scheduler retry, artifact, and alert ownership must stay outside read-only web request handling.",
        ],
        "required_next_step": decision["required_next_step"],
        "manual_next_step": decision["manual_next_step"],
        "references": list(DEFAULT_DECISION_REFERENCES),
        "secrets_policy": "decision_metadata_only_no_env_values",
    }
    _assert_secret_free(report)
    return report


def render_server_scheduler_deployment_target_decision_markdown(report: Mapping[str, object]) -> str:
    _assert_secret_free(report)
    lines = [
        "# Server Scheduler Deployment Target Decision",
        "",
        f"- decision status: `{report.get('decision_status', '')}`",
        f"- recommended target: `{report.get('recommended_target', '')}`",
        f"- zero budget required: `{str(report.get('zero_budget_required')).lower()}`",
        f"- hosted database configured: `{str(report.get('hosted_database_configured')).lower()}`",
        f"- runtime host available: `{str(report.get('runtime_host_available')).lower()}`",
        f"- scheduler deployed: `{str(report.get('scheduler_deployed')).lower()}`",
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
            "- This decision does not deploy a scheduler.",
            "- It does not create GitHub Actions workflow files.",
            "- It does not execute `launchctl`, cron, systemd, kubectl, or managed scheduler commands.",
            "",
        ]
    )
    return "\n".join(lines)


def _build_candidate_matrix(
    *,
    repo_visibility: str,
    zero_budget_required: bool,
    hosted_database_configured: bool,
    runtime_host_available: bool,
    mac_host_scheduler_allowed: bool,
    kubernetes_cluster_available: bool,
    managed_scheduler_free_tier_confirmed: bool,
    github_actions_allowed: bool,
) -> list[dict[str, object]]:
    github_free_fit = repo_visibility == "public" and zero_budget_required
    return [
        _candidate(
            target="github_actions_scheduled_workflow",
            zero_budget_fit=github_free_fit,
            current_ready=bool(
                github_actions_allowed
                and github_free_fit
                and hosted_database_configured
            ),
            can_reach_current_local_db=False,
            requires=[
                "public_repo_or_free_minutes",
                "hosted_database_or_network_reachable_runtime",
                "repository_secrets",
            ],
            reason=(
                "Best future zero-server scheduler once hosted DB/runtime exists."
                if github_actions_allowed and github_free_fit
                else "Not preferred under current repository/budget constraints."
            ),
        ),
        _candidate(
            target="vps_systemd_timer",
            zero_budget_fit=zero_budget_required and runtime_host_available,
            current_ready=runtime_host_available,
            can_reach_current_local_db=runtime_host_available and hosted_database_configured,
            requires=[
                "existing_server_or_already_paid_host",
                "repo_checkout",
                "repo_outside_runtime_env",
                "systemd_user_or_system_timer_permission",
            ],
            reason=(
                "Best when an existing server already hosts the DB/runtime."
                if runtime_host_available
                else "Requires an existing server; none is configured."
            ),
        ),
        _candidate(
            target="kubernetes_cronjob",
            zero_budget_fit=zero_budget_required and kubernetes_cluster_available,
            current_ready=kubernetes_cluster_available and hosted_database_configured,
            can_reach_current_local_db=False,
            requires=[
                "existing_cluster",
                "container_image",
                "secret_mount",
                "network_reachable_database",
            ],
            reason=(
                "Valid only if a cluster already exists."
                if kubernetes_cluster_available
                else "Too much infrastructure for current local MVP."
            ),
        ),
        _candidate(
            target="managed_scheduler",
            zero_budget_fit=managed_scheduler_free_tier_confirmed,
            current_ready=managed_scheduler_free_tier_confirmed and hosted_database_configured,
            can_reach_current_local_db=False,
            requires=[
                "confirmed_free_tier",
                "hosted_worker_or_network_endpoint",
                "secret_storage",
            ],
            reason=(
                "Possible only with a confirmed free tier and hosted runtime."
                if managed_scheduler_free_tier_confirmed
                else "Free tier/runtime is not confirmed."
            ),
        ),
        _candidate(
            target="local_host_scheduler",
            zero_budget_fit=True,
            current_ready=mac_host_scheduler_allowed,
            can_reach_current_local_db=True,
            requires=[
                "mac_is_on",
                "local_repo_checkout",
                "local_runtime_env",
                "operator_accepts_local_host_scheduler",
            ],
            reason=(
                "Only immediate free option that can reach current local DB."
                if mac_host_scheduler_allowed
                else "Blocked because local host scheduler is not the desired server-side path."
            ),
        ),
    ]


def _candidate(
    *,
    target: str,
    zero_budget_fit: bool,
    current_ready: bool,
    can_reach_current_local_db: bool,
    requires: list[str],
    reason: str,
) -> dict[str, object]:
    return {
        "target": target,
        "zero_budget_fit": zero_budget_fit,
        "current_ready": current_ready,
        "can_reach_current_local_db": can_reach_current_local_db,
        "requires": requires,
        "status": "ready_for_next_manifest_task" if current_ready else "blocked",
        "reason": reason,
    }


def _select_decision(candidates: list[dict[str, object]]) -> dict[str, object]:
    by_target = {str(candidate["target"]): candidate for candidate in candidates}
    if by_target["vps_systemd_timer"]["current_ready"] is True:
        return _ready_decision("vps_systemd_timer")
    if by_target["github_actions_scheduled_workflow"]["current_ready"] is True:
        return _ready_decision("github_actions_scheduled_workflow")
    if by_target["kubernetes_cronjob"]["current_ready"] is True:
        return _ready_decision("kubernetes_cronjob")
    if by_target["managed_scheduler"]["current_ready"] is True:
        return _ready_decision("managed_scheduler")
    if by_target["local_host_scheduler"]["current_ready"] is True:
        return {
            "recommended_target": "local_host_scheduler",
            "decision_status": "ready_for_local_only_scheduler_manifest_task",
            "blocking_reasons": [],
            "required_next_step": "local-host-scheduler-manifest-task",
            "manual_next_step": "local-host-scheduler-manifest-task",
        }
    return {
        "recommended_target": "github_actions_scheduled_workflow_after_hosted_runtime",
        "decision_status": "blocked_missing_hosted_database_or_runtime",
        "blocking_reasons": [
            "external_scheduler_cannot_reach_current_local_postgres",
            "hosted_database_not_configured",
            "runtime_host_not_available",
            "local_host_scheduler_not_allowed_for_server_side_path",
        ],
        "required_next_step": "hosted-database-runtime-decision",
        "manual_next_step": "hosted-database-runtime-decision",
    }


def _ready_decision(target: str) -> dict[str, object]:
    return {
        "recommended_target": target,
        "decision_status": "ready_for_scheduler_manifest_task",
        "blocking_reasons": [],
        "required_next_step": f"{target}-manifest-task",
        "manual_next_step": f"{target}-manifest-task",
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
    for token in FORBIDDEN_DEPLOYMENT_DECISION_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("server scheduler deployment decision payload contains secret-like value.")
