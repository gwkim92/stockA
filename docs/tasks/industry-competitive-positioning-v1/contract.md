# Task Contract

## Task

- 이름: industry-competitive-positioning-v1
- 요청: 전문 애널리스트식 산업 경쟁 분석 레이어를 기존 재무/피어/밸류에이션 기반에 추가한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations industry-competitive-positioning-run --as-of-date YYYY-MM-DD`가 기존 peer relative, financial metric, sector membership을 읽어 종목별 경쟁 포지션과 Porter-style 경쟁 압력 proxy를 `research.industry_competitive_position`에 저장할 수 있다.

## Scope

- 포함:
  - `research.industry_competitive_position` schema 추가
  - peer/financial/sector 기반 deterministic competitive positioning runner
  - CLI와 cadence/profile 연결
  - unit/CLI/cadence/orchestrator tests
  - task handoff 갱신
- 제외:
  - 유료 시장점유율 데이터
  - 실제 Porter Five Forces를 수작업으로 확정하는 analyst workflow
  - 추천 score/weight 변경
  - benchmark/evaluation split 변경
  - broker/order submit
  - frontend redesign

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/0022_industry_competitive_positioning.sql`
  - `src/stockanalysis/operations/industry_competitive_positioning.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_industry_competitive_positioning.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/industry-competitive-positioning-v1/*`
- 수정 금지 파일:
  - recommendation scoring weights
  - benchmark/evaluation split
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_industry_competitive_positioning tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_migrations.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task industry-competitive-positioning-v1`

## Done Criteria

- [ ] 산업 경쟁 포지션 table이 migration으로 추가된다.
- [ ] runner가 peer group, sector membership, peer relative metrics를 읽는다.
- [ ] runner는 pricing power, profitability, financial strength, capacity-cycle risk, competitive position을 저장한다.
- [ ] `--execute`는 `ops.pipeline_run`을 기록하고 idempotent upsert를 수행한다.
- [ ] 추천 score/weight, benchmark, broker/order flow는 변경되지 않는다.
