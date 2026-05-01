# Macro Batch Upsert

## Goal

이 문서는 여러 기본 거시 series를 한 번에 canonical Postgres에 적재하는 `macro-batch-upsert` 경로를 정의한다.

현재 구현 범위:

- 기본 macro series 목록 또는 일부 선택
- fixture directory 기반 deterministic batch 실행
- series별 독립 `pipeline_run`
- 전체 batch summary 출력

## Why Batch Exists

single-series `macro-upsert`만으로는 초기 macro bootstrap이 비효율적이다.

batch 단계에서 필요한 것은:

- 여러 series 연속 적재
- series별 성공/실패 구분
- 운영자가 한 번에 bootstrap 상태를 확인할 수 있는 summary

## Current Flow

1. CLI가 요청한 default series 목록을 해석한다.
2. `--fixtures-dir`가 있으면 `fred_series_<ID>.json`, `fred_observations_<ID>.json`를 찾는다.
3. 각 series에 대해 기존 `macro-upsert` runner를 순차 실행한다.
4. 각 series는 독립 `pipeline_run`을 만든다.
5. CLI는 전체 성공/실패 개수와 per-series 결과를 JSON으로 출력한다.

## CLI

특정 series만 실행:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-batch-upsert \
  --fixtures-dir tests/fixtures \
  --series-id CPIAUCSL \
  --series-id FEDFUNDS
```

기본 전체 세트 실행:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-batch-upsert
```

## Summary Shape

현재 출력은 아래 필드를 가진다.

- `requested_series_count`
- `succeeded_series_count`
- `failed_series_count`
- `total_observation_count`
- `results`

`results` 각 항목은:

- 성공 시 `series_id`, `run_id`, `observation_count`, `status="succeeded"`
- 실패 시 `series_id`, `error`, `status="failed"`

## Verification

현재 검증 명령:

```bash
bash scripts/verify_macro_batch_upsert.sh
```

이 검증은:

- docker Postgres migration + seed
- 2-series fixture batch upsert
- `macro.series`, `macro.observation`, `source_run_id`, `ops.pipeline_run` 확인

을 수행한다.

## Current Limits

아직 구현하지 않은 것:

- parallel batch execution
- custom non-default series batch
- live FRED smoke를 포함한 end-to-end 검증
- retry/backoff orchestration

## Next Step

다음으로 자연스러운 확장:

1. `macro-run-history-report`
2. `macro-batch-retry-policy`
3. `sec-filings-ingest`
