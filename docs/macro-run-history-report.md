# Macro Run History Report

## Goal

이 문서는 최근 macro upsert 실행 이력을 canonical Postgres에서 조회하는 `macro-run-history` 경로를 정의한다.

현재 구현 범위:

- recent macro upsert run 목록
- status 집계
- per-run observation count
- batch 적재 이후 audit 조회

## Why This Step Exists

적재가 된다는 것과 잘 되고 있는지 계속 검토할 수 있다는 것은 다르다.

이 단계에서 필요한 것은:

- 최근 run 이력 확인
- 어떤 series가 성공/실패했는지 확인
- 각 run이 몇 개 observation을 남겼는지 확인

즉 이 기능은 macro ingest 운영 상태를 보는 첫 audit/report 계층이다.

## Current Flow

1. CLI가 최근 조회 limit와 optional status filter를 받는다.
2. Postgres에서 `ops.pipeline_run`과 `macro.observation.source_run_id`를 조합해 report JSON을 만든다.
3. Python은 JSON을 parse해서 그대로 출력한다.

## CLI

최근 5건 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-run-history --limit 5
```

성공 run만 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-run-history --status succeeded
```

## Report Shape

현재 출력은 아래 필드를 가진다.

- `pipeline_name`
- `limit`
- `status_filter`
- `run_count`
- `status_counts`
- `runs`

각 `runs` 항목은:

- `run_id`
- `status`
- `series_id`
- `loaded_series_codes`
- `region_code`
- `category`
- `started_at`
- `ended_at`
- `observation_count`
- `first_observation_date`
- `last_observation_date`
- `error_summary`

## Verification

현재 검증 명령:

```bash
bash scripts/verify_macro_run_history_report.sh
```

이 검증은:

- docker Postgres migration + seed
- 2-series fixture batch upsert
- `macro-run-history` JSON 출력 검증

을 수행한다.

## Current Limits

아직 구현하지 않은 것:

- batch 상위 엔터티 수준 report
- 장기 집계 지표
- UI visualization
- live FRED smoke를 포함한 end-to-end 검증

## Next Step

다음으로 자연스러운 확장:

1. `macro-batch-retry-policy`
2. `sec-filings-ingest`
3. `market-data-ingest`
