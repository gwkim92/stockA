# Review

## Scope Reviewed

- `src/stockanalysis/performance/outcome.py`
- `src/stockanalysis/ingest/cli.py`
- `tests/test_performance_outcome_bootstrap.py`
- `tests/test_ingest_cli.py`
- `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
- `tests/fixtures/alpha_vantage_daily_adjusted_SPY.json`
- `scripts/verify_performance_outcome_bootstrap.sh`
- `docs/performance-outcome-bootstrap.md`
- `docs/verification-plan.md`
- `docs/tasks/long-horizon-outcome-runner/`

## Findings

- blocking finding 없음.
- schema 변경 없이 기존 `(recommendation_id, measurement_end_date)` unique 구조로 multiple horizon outcome을 저장한다.
- batch runner는 단일 outcome runner를 재사용해 계산/DB write logic을 중복하지 않는다.
- Docker Postgres 검증에서 2024-11-04 outcome과 2024-12-02 outcome 2건이 확인됐다.

## Verification

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_performance_outcome_bootstrap tests.test_ingest_cli -v`: 44 tests 통과
- `bash -n scripts/verify_performance_outcome_bootstrap.sh`: 통과
- `bash scripts/verify_performance_outcome_bootstrap.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task long-horizon-outcome-runner`: 통과

## Residual Risk

- 실제 장기 horizon과 scheduler는 아직 별도 작업이 필요하다.
- 실거래 PnL과 portfolio attribution은 아직 범위 밖이다.
