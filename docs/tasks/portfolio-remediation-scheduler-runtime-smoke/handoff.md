# Session Handoff

## Active Task

- 이름: portfolio-remediation-scheduler-runtime-smoke
- 담당: Codex
- 날짜: 2026-04-30

## Current Status

- 완료:
  - Docker Postgres runtime smoke script를 추가했다.
  - scheduler wrapper run mode가 daily remediation runner를 실행하고 JSON/stderr artifact를 생성하는지 검증했다.
  - BABA open remediation ticket과 latest DB pipeline run status `succeeded`를 검증했다.
  - README, verification plan, scheduler activation/install docs를 갱신했다.
- 막힌 점:
  - production DB smoke와 actual launchd install은 이번 범위 밖이다.

## Files Touched

- 생성:
  - `docs/plans/2026-04-30-portfolio-remediation-scheduler-runtime-smoke.md`
  - `docs/portfolio-remediation-scheduler-runtime-smoke.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/contract.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/plan.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/handoff.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/review.md`
  - `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`
- 수정:
  - `README.md`
  - `docs/portfolio-remediation-scheduler-activation.md`
  - `docs/portfolio-remediation-scheduler-install.md`
  - `docs/verification-plan.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/contract.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/handoff.md`
  - `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/review.md`

## Decisions

- runtime smoke는 Docker Postgres에서 수행한다.
- production DB와 actual host scheduler install은 범위 밖이다.
- external alert destination은 아직 붙이지 않는다.
- scheduler wrapper는 temp artifact root에 stdout JSON과 stderr log를 남기는 방식으로 검증한다.
- smoke payload의 최소 운영 신호는 BABA open `thesis_remediation` ticket과 latest daily automation `succeeded` run이다.

## Verification Already Run

- `bash -n scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`: 통과
- `bash -n scripts/run_portfolio_remediation_daily_scheduler.sh`: 통과
- `bash scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`: sandbox Docker socket permission denied 확인 후 sandbox 밖 재실행 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-scheduler-runtime-smoke`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- production DB runtime smoke
- actual host launchd install
- `launchctl bootstrap`
- external alert destination
- market holiday calendar integration

## Exact Next Step

- 다음 세션은 이것부터 시작: intended runtime env file을 만들고 실제 의도한 runtime DB에서 `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode를 1회 실행한 뒤, 통과하면 별도 승인으로 `scripts/install_portfolio_remediation_scheduler.sh --install --env-file <env>`와 `launchctl bootstrap`을 진행한다.

## Risks

- Docker socket 권한은 sandbox 밖 실행이 필요할 수 있다.
- Docker smoke는 production DB 품질을 보장하지 않는다.
- alert destination과 market holiday skip rule이 아직 없으므로 unattended 운영 준비는 미완성이다.
