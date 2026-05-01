# Task Contract

## Task

- 이름: benchmark-outcome-alpha
- 요청: benchmark ETF price가 있을 때 성과 outcome에 benchmark return, alpha, outperform label을 저장하고 검증한다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `performance-outcome-bootstrap` Docker 검증이 SPY benchmark price를 포함하고, AAPL outcome에 `benchmark_return_pct = 0.005000`, `alpha_pct = 0.005000`, `outcome_label = outperform`을 확인한다.

## Why

- 성과 추적은 absolute return만으로는 부족하다. 중장기 추천 품질은 시장/benchmark 대비 초과성과를 함께 봐야 한다.

## Scope

- 포함:
  - benchmark 포함 SEC universe fixture
  - SPY daily adjusted price fixture
  - benchmark/alpha unit test
  - performance Docker verify benchmark assertion
  - docs/task handoff 갱신
- 제외:
  - recommendation scoring 변경
  - thesis generation 변경
  - benchmark policy engine
  - 실거래 PnL
  - portfolio attribution

## Mutable Surface

- 수정 가능한 파일:
  - `docs/performance-outcome-bootstrap.md`
  - `docs/plans/2026-04-27-benchmark-outcome-alpha.md`
  - `docs/tasks/benchmark-outcome-alpha/`
  - `docs/tasks/performance-outcome-bootstrap/handoff.md`
  - `docs/verification-plan.md`
  - `scripts/verify_performance_outcome_bootstrap.sh`
  - `tests/fixtures/sec_company_tickers_exchange_with_benchmark_sample.json`
  - `tests/fixtures/alpha_vantage_daily_adjusted_SPY.json`
  - `tests/test_performance_outcome_bootstrap.py`
- 수정 금지 파일:
  - recommendation score formula
  - thesis generation rule
  - portfolio review action rule
  - DB schema unless verification proves current schema cannot support alpha
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_performance_outcome_bootstrap.sh`
  - `bash scripts/verify_performance_outcome_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task benchmark-outcome-alpha`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Completion Criteria

- [x] benchmark fixture가 데이터 수집기 경로로 canonical instrument/price에 들어간다.
- [x] unit test가 alpha/outperform 계산을 고정한다.
- [x] Docker verify가 actual DB row의 benchmark return과 alpha를 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Verification Plan

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash -n scripts/verify_performance_outcome_bootstrap.sh`
- `bash scripts/verify_performance_outcome_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task benchmark-outcome-alpha`
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Risks

- SPY를 universe에 넣으면 strategy universe member는 늘 수 있다. 다만 recommendation은 theme/cycle evidence가 필요한 구조라 SPY recommendation은 생기지 않아야 한다.
- 현재 benchmark fixture는 짧은 3일 horizon이다. 장기 benchmark 성과는 후속 작업이다.
