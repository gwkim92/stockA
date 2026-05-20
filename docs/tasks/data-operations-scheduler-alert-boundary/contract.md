# Task Contract

## Task

- 이름: data-operations-scheduler-alert-boundary
- 요청: actual scheduler activation 전에 failed/stale/missing/timeout/artifact/preflight 상태를 secret-free alert rule reference로 고정한다.
- 담당: Codex
- 날짜: 2026-05-06

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Data Operations Loop용 Prometheus-compatible alert rule reference와 validator가 존재하고, Alertmanager receiver나 secret이 없이 failed/stale/missing/timeout/artifact/preflight 상태를 운영자가 볼 수 있다.

## Why

- scheduler를 켠 뒤 실패 알림 경계가 없으면 freshness 회복과 rerun 판단이 늦어진다.
- actual receiver 연결은 secret/webhook/routing을 포함하므로 별도 승인 전에는 rule reference와 validator만 만든다.

## Scope

- 포함:
  - `ops/observability/data-operations-alert-rules.yml`
  - secret-free alert rule validator
  - verification script
  - docs/task handoff/roadmap 갱신
- 제외:
  - Alertmanager receiver routing
  - Slack/email/PagerDuty/Opsgenie/webhook config
  - production Prometheus install
  - actual scheduler activation
  - provider network credential validation
  - DB schema changes
  - write APIs, RBAC, broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `ops/observability/data-operations-alert-rules.yml`
  - `scripts/validate_data_operations_alert_rules.py`
  - `scripts/verify_data_operations_scheduler_alert_boundary.sh`
  - `docs/data-operations-scheduler-alert-boundary.md`
  - `docs/data-operations-scheduler-install-dry-run.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_artifact_runner.sh`
  - `scripts/verify_data_operations_runtime_env_readiness.sh`
  - `scripts/verify_data_operations_runtime_smoke.sh`
  - `scripts/verify_data_operations_cadence_foundation.sh`
  - `scripts/verify_data_operations_scheduler_activation_boundary.sh`
  - `scripts/verify_data_operations_scheduler_install_dry_run.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-06-data-operations-scheduler-alert-boundary.md`
  - `docs/tasks/data-operations-scheduler-alert-boundary/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_scheduler_alert_boundary.sh`
  - `bash scripts/verify_data_operations_scheduler_install_dry_run.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `/tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-scheduler-alert-boundary`
  - `git diff --check`

## Deliverables

- Data operations alert rule reference
- Alert rule validator
- Verification script
- Docs and handoff updates

## Completion Criteria

- [x] six alert rules exist in stable order.
- [x] rules cover missing, failed, stale, timeout, artifact missing, and scheduler preflight failures.
- [x] rule file contains no receiver/webhook/secret destination.
- [x] validator checks allowed metric names and bounded labels.
- [x] docs state receiver routing remains future work.
- [x] roadmap moves fixed next task after completion.
- [x] verification commands pass and evidence is recorded.

## Risks

- This does not connect a real receiver.
- This assumes a future exporter emits the documented metrics.
- Actual scheduler activation remains out of scope.
