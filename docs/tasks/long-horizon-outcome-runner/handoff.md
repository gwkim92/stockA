# Session Handoff

## Active Task

- 이름: long-horizon-outcome-runner
- 담당: Codex
- 날짜: 2026-04-27

## Current Status

- 완료:
  - 여러 measurement horizon을 저장하는 `performance-outcome-batch-bootstrap` runner와 CLI를 추가했다.
  - 2024-11-04 short horizon과 2024-12-02 31일 horizon outcome을 Docker Postgres에서 검증했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-27-long-horizon-outcome-runner.md`
  - `docs/tasks/long-horizon-outcome-runner/contract.md`
  - `docs/tasks/long-horizon-outcome-runner/plan.md`
  - `docs/tasks/long-horizon-outcome-runner/handoff.md`
  - `docs/tasks/long-horizon-outcome-runner/review.md`
- 수정:
  - `README.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/verification-plan.md`
  - `scripts/verify_performance_outcome_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/outcome.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
  - `tests/fixtures/alpha_vantage_daily_adjusted_SPY.json`
  - `tests/test_ingest_cli.py`
  - `tests/test_performance_outcome_bootstrap.py`

## Decisions

- schema 변경 없이 기존 unique `(recommendation_id, measurement_end_date)`를 활용한다.
- batch runner는 단일 runner를 재사용한다.
- horizon day는 calendar day로 계산하고 trading day 보정은 기존 latest-on-or-before price lookup에 맡긴다.

## Verification Already Run

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_performance_outcome_bootstrap tests.test_ingest_cli -v`: 44 tests 통과
- `bash -n scripts/verify_performance_outcome_bootstrap.sh`: 통과
- `bash scripts/verify_performance_outcome_bootstrap.sh`: 통과
  - Docker Postgres에서 전체 187 tests와 outcome 2건 assertion을 함께 확인했다.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task long-horizon-outcome-runner`: 통과

## Still Unverified

- 실제 90/180/365일 장기 가격 history 기반 outcome
- cron/scheduled 자동 실행
- 실거래 체결 기준 PnL
- portfolio attribution

## Exact Next Step

- 다음 세션은 이것부터 시작: portfolio attribution bootstrap 또는 scheduled outcome runner를 구현한다.

## Risks

- fixture horizon은 31일이라 실제 장기 투자 검증은 아니다.
- scheduler/automation은 아직 없다.
