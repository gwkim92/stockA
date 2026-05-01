# Session Handoff

## Active Task

- 이름: scheduled-outcome-runner
- 담당: Codex
- 날짜: 2026-04-27

## Current Status

- 완료:
  - due horizon candidate lookup을 추가했다.
  - `performance-outcome-schedule-bootstrap` runner와 CLI를 추가했다.
  - schedule parent pipeline run과 candidate-level failure summary를 추가했다.
  - Docker Postgres에서 schedule CLI가 AAPL 3일/31일 outcome 2건을 생성하는지 검증했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-27-scheduled-outcome-runner.md`
  - `docs/scheduled-outcome-runner.md`
  - `docs/tasks/scheduled-outcome-runner/contract.md`
  - `docs/tasks/scheduled-outcome-runner/plan.md`
  - `docs/tasks/scheduled-outcome-runner/handoff.md`
  - `docs/tasks/scheduled-outcome-runner/review.md`
  - `scripts/verify_scheduled_outcome_runner.sh`
- 수정:
  - `README.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/outcome.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_performance_outcome_bootstrap.py`

## Decisions

- schedule runner는 기존 outcome calculation을 재사용한다.
- default horizon은 30/90/180/365 calendar days다.
- OS cron 또는 app automation은 이번 범위가 아니다.
- candidate 중 하나라도 실패하면 parent run은 failed가 되지만, 성공한 child outcome은 유지한다.

## Verification Already Run

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_performance_outcome_bootstrap tests.test_ingest_cli -v`: 54 tests 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 205 tests 통과
- `bash -n scripts/verify_scheduled_outcome_runner.sh`: 통과
- `bash scripts/verify_scheduled_outcome_runner.sh`: 통과
  - 첫 실행은 sandbox Docker socket 권한으로 실패했고, 승인된 권한으로 재실행해 통과했다.
  - Docker Postgres에서 전체 205 tests와 scheduled outcome assertion을 함께 확인했다.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task scheduled-outcome-runner`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- 실제 90/180/365일 장기 가격 history 기반 scheduled outcome
- OS-level cron 또는 heartbeat automation
- failed candidate retry/report

## Exact Next Step

- 다음 세션은 이것부터 시작: outcome 없는 position coverage report 또는 실제 recurring automation 연결을 구현한다.

## Risks

- price data가 없는 due horizon은 실패 candidate로 남는다.
- schedule runner 자체는 price backfill을 수행하지 않는다.
