# Session Handoff

## Current Status

- 진행 중: benchmark composition CSV import runner, CLI command, unit/CLI tests를 추가했다. 로컬 focused tests와 full unittest는 통과했고 EC2 smoke가 남아 있다.

- 구현 중: task contract를 만들었고 benchmark composition CSV import runner, CLI command, unit/CLI tests를 추가했다. 로컬 focused tests는 통과했고 전체 검증/EC2 smoke가 남아 있다.

## Implementation Notes

- 새 runner: `src/stockanalysis/operations/benchmark_composition_import.py`
  - repo-outside CSV를 읽는다.
  - required columns: `symbol`, `target_weight`
  - optional columns: `name`, `rationale`
  - duplicate symbol, missing/invalid/negative/out-of-range target weight를 차단한다.
  - `coverage_status`를 `partial_holdings_only` 또는 `full_enough_for_drift`로 구분한다.
  - `--execute`일 때만 `ops.pipeline_run`과 `ref.benchmark_composition` upsert를 수행한다.
- 새 CLI: `stockanalysis-operations benchmark-composition-import-run`
  - `--source-type operator_upload|provider_file`
  - `--min-full-coverage-weight` 기본값 `0.9500`
- 추가 테스트:
  - `tests/test_benchmark_composition_import.py`
  - `tests/test_data_operations_cli.py`

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: 전체 로컬 검증을 실행하고 EC2에서 repo-outside holdings CSV smoke를 수행한다.
