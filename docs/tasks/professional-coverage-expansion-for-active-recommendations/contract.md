# Task Contract

## Task

- 이름: professional-coverage-expansion-for-active-recommendations
- 요청: active recommendation gap symbols부터 SEC/companyfacts, normalized metrics, peer relative, valuation, industry competitive position, equity research artifact coverage를 넓힌다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations professional-coverage-expansion-run --as-of-date YYYY-MM-DD --execute`가 active recommendation coverage gap symbols를 찾고, SEC `company_tickers_exchange`로 CIK를 해석한 뒤 companyfacts 수집, financial metric normalization, peer relative analysis, valuation snapshot, industry competitive positioning, equity research reporting을 순서대로 실행한다.

## Scope

- 포함:
  - SEC `company_tickers_exchange` 공개 mapping으로 active recommendation gap symbol의 CIK 해석
  - SEC companyfacts upsert의 symbol fallback
  - 새 operations runner/CLI `professional-coverage-expansion-run`
  - weekly `sec-filings-weekly` profile과 cadence registry 연결
  - unit/CLI/orchestrator tests
  - task handoff
- 제외:
  - 추천 score formula/weight 변경
  - benchmark/evaluation split 변경
  - 유료 데이터 공급자 도입
  - 실거래 broker submit
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/operations/professional_coverage_expansion.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cadence.py`
  - `tests/test_sec_companyfacts.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_professional_coverage_expansion.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/project-execution-roadmap.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `AGENTS.md`
  - `docs/tasks/professional-coverage-expansion-for-active-recommendations/*`
- 수정 금지 파일:
  - recommendation score formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_ingest_cli tests.test_data_operations_cadence tests.test_sec_companyfacts tests.test_professional_coverage_expansion tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-coverage-expansion-for-active-recommendations`

## Done Criteria

- dry-run은 SEC 호출 대상과 downstream planned steps를 JSON으로 설명한다.
- execute는 selected CIK에 대해 companyfacts를 upsert하고, 기존 professional analysis runner들을 순서대로 실행한다.
- 같은 기능은 weekly profile에서 자동 실행 후보로 포함된다.
- 추천 weight는 변경하지 않는다.
