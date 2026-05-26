# news-intraday-scheduler-failure-remediation-v1 Contract

## Task Request

- request: Fix the EC2 `news-intraday` scheduler failure so short-cycle news collection and analysis can run automatically again.
- context: EC2 profile scheduler is installed and timers are active, but `stockanalysis-operating-data-news-intraday.service` last result is `exit-code`.

## Goal

- goal: Diagnose the failed `news-intraday` systemd profile, fix the underlying backend/runtime/env issue, rerun it successfully, and expose healthy status through `/api/data-health`.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/`
  - `docs/tasks/news-intraday-scheduler-failure-remediation-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`

## Scope

- Inspect EC2 `journalctl` logs for `stockanalysis-operating-data-news-intraday.service`.
- Identify whether the failure is caused by runtime env, provider budget, RSS/news ingestion, AI fallback, DB schema, CLI/profile orchestration, or timeout.
- Fix through backend CLI/service boundary where possible.
- Rerun `news-intraday` once manually or by `systemctl start`, then refresh scheduler status and data-health.

## Non-Goals

- No recommendation score weight changes.
- No broker/order enablement.
- No paid provider requirement.
- No manual DB edits that bypass backend service boundaries.
- No broad scheduler redesign unless the failure proves the current profile boundary is structurally wrong.

## Verification Commands

- verification command: inspect `journalctl -u stockanalysis-operating-data-news-intraday.service`.
- verification command: run focused Python tests for any changed operations/profile code.
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-intraday-scheduler-failure-remediation-v1`
- EC2 verification: `systemctl --no-pager --plain status stockanalysis-operating-data-news-intraday.service` and `/api/data-health` scheduler profile result.

## Acceptance Criteria

- The root cause of the `news-intraday` failure is documented.
- A code/config fix or durable operator decision is recorded.
- EC2 `news-intraday` rerun succeeds or the profile is explicitly disabled with a documented safe reason.
- `/api/data-health` no longer presents the failure as an unexplained operational state.
