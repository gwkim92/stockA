# live-ai-invocation-health-current-failure-v2 Contract

## Task Request

- request: `/api/data-health`의 `live_ai_invocation_health_attention` gate를 닫기 위해 최신 Codex OAuth AI 호출 실패 원인을 확인하고 복구한다.
- context: 현재 EC2 `/api/data-health`는 `status=critical_ai_failed`, `critical_latest_unhealthy_count=2`, latest failed task `news-rss-ai-extract`, error code `codex_oauth_auth_invalid`를 반환한다.

## Goal

- goal: 최신 critical AI 작업인 뉴스 한국어 번역과 뉴스 AI 구조화가 EC2에서 성공하도록 만들고, `/api/data-health.open_gates`에서 `live_ai_invocation_health_attention`이 제거되었음을 검증한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/live-ai-invocation-health-current-failure-v2/*`
  - `src/stockanalysis/ingest/news/translation.py`
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - related tests.

## Scope

- Inspect EC2 `ai.model_invocation` latest failures.
- Inspect EC2 Codex OAuth runtime status without printing secrets.
- Add a non-OAuth OpenAI Agents SDK provider path for news translation and news AI extraction when `STOCKANALYSIS_LLM_PROVIDER=agents_sdk_openai`.
- Update live AI health to count both `codex_oauth` and `agents_sdk_openai` model invocations.
- Rerun limited AI smoke or relevant operating profile after authentication/runtime is valid.
- Update handoff with exact evidence.

## Non-Goals

- Do not delete failed model_invocation rows unless a separate data cleanup task is explicitly approved.
- Do not weaken translation/AI validators.
- Do not hide current failures by changing UI wording only.
- Do not change recommendation weights, benchmark definitions, portfolio positions, schema, scheduler cadence, or broker/order boundaries.

## Verification Commands

- verification command: EC2 `/api/data-health` authorized smoke.
- verification command: EC2 relevant AI runner/profile smoke.
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task live-ai-invocation-health-current-failure-v2`
- verification command: `git diff --check`

## Acceptance Criteria

- Root cause is documented with current evidence.
- Latest critical monitored AI task statuses are no longer failed.
- `/api/data-health.open_gates` no longer includes `live_ai_invocation_health_attention`, or the handoff clearly states the external blocker requiring user action.
- No unrelated scoring/order/portfolio behavior is changed.
