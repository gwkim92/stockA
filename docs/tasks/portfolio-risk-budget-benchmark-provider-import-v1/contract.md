# Task Contract

## Task

- 이름: portfolio-risk-budget-benchmark-provider-import-v1
- 요청: partial manual seed를 넘어, 무료 provider file 또는 operator upload CSV로 dated benchmark holdings를 `ref.benchmark_composition`에 적재하는 backend CLI를 만든다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations benchmark-composition-import-run --holdings-csv ... --benchmark-code SPY --source-name ... --source-as-of-date YYYY-MM-DD --execute`가 repo 밖 CSV를 검증한 뒤 `ref.benchmark_composition`에 dated holdings를 upsert하고, coverage가 충분하지 않으면 full benchmark drift로 해석하지 않도록 import report에 명시한다.

## Scope

- 포함:
  - repo-outside holdings CSV parser
  - required columns: `symbol`, `target_weight`
  - optional columns: `name`, `rationale`
  - row validation: duplicate symbol, invalid weight, negative weight, total weight, min coverage threshold
  - preview-first runner with `--execute`
  - `operator_upload` / `provider_file` source type support
  - SQL upsert into `ref.benchmark_composition`
  - CLI command and tests
  - EC2 smoke with repo-outside fixture upload
- 제외:
  - paid provider API
  - web upload UI
  - recommendation weight changes
  - broker submit/live order flow
  - automatic drift interpretation change beyond recorded coverage flags

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/benchmark_composition_import.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_benchmark_composition_import.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/portfolio-risk-budget-benchmark-provider-import-v1/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - kill switch unlock
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_import tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-benchmark-provider-import-v1`

## Done Criteria

- CLI dry-run validates CSV and prints a secret-free report without DB mutation.
- CLI execute upserts rows and records `ops.pipeline_run`.
- Import report distinguishes partial vs full-enough coverage.
- Invalid CSV input fails before mutation.
- No recommendation weight, broker submit, live order, or kill switch behavior changes.
