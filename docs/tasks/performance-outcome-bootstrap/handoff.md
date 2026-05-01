# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: performance-outcome-bootstrap
- 담당: Codex
- 날짜: 2026-04-26

## Current Status

- 완료:
  - recommendation과 thesis의 사후 가격 성과를 `performance.recommendation_outcome`, `performance.thesis_outcome`에 저장하는 bootstrap 경로를 추가했다.
  - AAPL fixture 기준으로 2024-11-01 entry price `222.9100`에서 2024-11-04 exit price `225.1391`까지 absolute return `0.010000`을 검증했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `db/migrations/0010_performance_outcome.sql`
  - `docs/plans/2026-04-26-performance-outcome-bootstrap.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/tasks/performance-outcome-bootstrap/contract.md`
  - `docs/tasks/performance-outcome-bootstrap/plan.md`
  - `docs/tasks/performance-outcome-bootstrap/handoff.md`
  - `docs/tasks/performance-outcome-bootstrap/review.md`
  - `scripts/verify_performance_outcome_bootstrap.sh`
  - `src/stockanalysis/performance/__init__.py`
  - `src/stockanalysis/performance/outcome.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
  - `tests/test_performance_outcome_bootstrap.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`

## Decisions

- 결정:
  - performance outcome은 추천/보유 판단을 변경하지 않고 사후 측정만 저장한다.
  - one recommendation can have multiple measurement dates via unique `(recommendation_id, measurement_end_date)`.
  - benchmark price가 없으면 benchmark return과 alpha는 null로 저장한다.
- 이유:
  - 성과 측정은 추천 로직과 분리되어야 retrospective evaluation이 가능하다.

## Verification Already Run

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_performance_outcome_bootstrap tests.test_ingest_cli -v`: 36 tests 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 179 tests 통과
- `bash -n scripts/verify_performance_outcome_bootstrap.sh`: 통과
- `bash scripts/verify_performance_outcome_bootstrap.sh`: 통과
  - 최초 sandbox 실행은 Docker socket 권한으로 실패했고, 승인된 Docker 권한으로 재실행해 통과했다.

## Still Unverified

- 항목: 장기 horizon outcome
- 왜 중요한가: 현재 fixture horizon은 2024-11-01부터 2024-11-04까지 3일로 짧다.

- 항목: 실거래 체결 기준 PnL
- 왜 중요한가: 현재 outcome은 adjusted close 기반 사후 측정이며 broker/trade execution 성과가 아니다.

## Exact Next Step

- 다음 세션은 이것부터 시작: 장기 horizon outcome runner 또는 portfolio attribution bootstrap을 추가한다.

## Risks

- 위험:
  - 가격 기준은 adjusted close 기반이라 intraday execution PnL과 다르다.
  - current fixture horizon은 짧아서 장기 성과 검증은 아니다.
- 대응:
  - longer horizon backfill은 후속 task로 분리한다.
  - real trade PnL은 broker/trade layer 이후 별도 performance task로 추가한다.
  - portfolio attribution은 performance outcome 위에 별도 `portfolio-attribution-bootstrap` task로 추가한다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/thesis.py`
  - `src/stockanalysis/ingest/market/price.py`
- 다시 찾기 싫은 배경지식:
  - current fixture chain에서 AAPL recommendation total score는 `0.3610`이다.
  - AAPL entry adjusted close on 2024-11-01 is `222.9100`.
  - outcome fixture는 2024-11-04 adjusted close `225.1391`로 absolute return `0.010000`을 만든다.
