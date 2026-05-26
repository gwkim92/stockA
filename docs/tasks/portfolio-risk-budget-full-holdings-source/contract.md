# Task Contract

## Task

- 이름: portfolio-risk-budget-full-holdings-source
- 요청: partial operator benchmark holdings를 full-enough 무료 provider holdings로 대체한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: State Street 공식 SPY daily holdings XLSX를 repo 밖에 저장하고, 이를 `symbol,target_weight,name,rationale` CSV로 정규화한 뒤 `ref.benchmark_composition`에 `provider_file` source로 적재해 coverage가 95% 이상이 된다.

## Scope

- 포함:
  - State Street SPY `Download All Holdings: Daily` XLSX parser
  - provider XLSX 다운로드를 repo 밖 raw artifact로 저장
  - normalized CSV를 repo 밖 artifact로 저장
  - 기존 benchmark composition import runner 재사용
  - dot class ticker를 canonical `-` class ticker로 정규화
  - 필요 시 missing benchmark component instrument를 명시적 옵션으로 생성
  - EC2에서 provider file import와 guardrail rerun smoke
- 제외:
  - 유료 provider
  - S&P index licensed composition 직접 사용
  - recommendation scoring weight 변경
  - benchmark/evaluation split 변경
  - broker submit/live order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/benchmark_composition_import.py`
  - `src/stockanalysis/operations/benchmark_composition_provider.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_benchmark_composition_import.py`
  - `tests/test_benchmark_composition_provider.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/portfolio-risk-budget-full-holdings-source/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_import tests.test_benchmark_composition_provider tests.test_data_operations_cli`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-full-holdings-source`
  - `git diff --check`

## Done Criteria

- Provider command downloads/parses official SPY holdings XLSX without new paid dependency.
- Normalized CSV coverage is at least 95%.
- EC2 import records `provider_file` source and guardrail rerun reports full-enough/calculated drift, not partial composition.
- Recommendation weights and broker/order behavior remain unchanged.
