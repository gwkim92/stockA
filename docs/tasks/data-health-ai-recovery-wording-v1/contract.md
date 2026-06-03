# data-health-ai-recovery-wording-v1 Contract

## Task Request

- request: `/data-health`에서 실제 AI 호출이 복구됐는데도 최근 48시간 누적 실패 수가 현재 장애처럼 보이는 문구를 정리한다.
- context: EC2 latest `news-intraday` run succeeded after translation grounding fix, but `/data-health` top card can still show `실제 AI 실패 17건` because `live_ai_invocation_health.recent_failed_count` is a rolling-window history.

## Goal

- goal: 사용자가 `현재 실패`, `과거 실패 기록`, `최신 실행 성공`, `AI 회귀평가 실패`를 구분해서 읽을 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/tasks/data-health-ai-recovery-wording-v1/*`

## Invariants

- Do not change FastAPI/API DTO contracts.
- Do not change data-health backend SQL or scheduler cadence.
- Do not change recommendation scoring weights, benchmark definitions, portfolio positions, broker/order flow, or live trading boundary.
- Do not hide real current AI failures. Only clarify recovered rolling-window failures.
- Do not expose DB URL, bearer token, OAuth token, webhook URL, or repo-outside paths.

## Scope

- Add display helpers that separate current failed task count from rolling-window failed invocation count.
- Update the top data quality metric copy.
- Update the live AI invocation rail labels from ambiguous `핵심 실패` to current-vs-history wording.
- Preserve existing section layout and styles.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-ai-recovery-wording-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] Recovered AI status no longer renders as a plain current failure count in the top card.
- [x] Live AI section shows current unhealthy task count separately from recent rolling-window failures.
- [x] Existing critical failure status still communicates failure.
- [x] Local verification passes.
- [x] EC2 route smoke confirms updated Korean copy renders.
