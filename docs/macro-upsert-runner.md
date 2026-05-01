# Macro Upsert Runner

## Goal

이 문서는 `macro-sync`가 만든 정규화 결과를 canonical Postgres에 실제 반영하는 첫 실행 경로를 정의한다.

현재 구현 범위:

- `psql` 명령 기반 DB 실행기
- `ops.pipeline_run` 생성
- `macro.series`, `macro.observation` upsert 실행
- 성공/실패 상태 갱신
- fixture 기반 integration 검증

## Why This Step Exists

`macro-ingest` 단계는 정규화와 SQL 생성까지만 고정했다.

다음으로 필요한 것은:

- 실제 canonical DB 반영
- ingest 실행 이력 기록
- 관측치와 pipeline run 연결

즉 이 단계는 `정규화 결과를 저장 가능한 상태`에서 `저장까지 실제 수행하는 상태`로 넘어가는 경계다.

## Current Flow

1. `macro-upsert` CLI가 FRED payload를 fixture 또는 live source에서 읽는다.
2. `ops.pipeline_run`에 `running` 상태 row를 만든다.
3. `render_macro_sync_sql(..., source_run_id=run_id)`를 실행한다.
4. 성공 시 pipeline run을 `succeeded`로 마감한다.
5. 실패 시 pipeline run을 `failed`로 갱신한다.

## Runtime Contract

이 실행기는 Python DB driver 대신 `psql` 명령을 사용한다.

필수 환경변수:

- `STOCKANALYSIS_PSQL_COMMAND`

예시:

```bash
export STOCKANALYSIS_PSQL_COMMAND="psql postgresql://postgres:postgres@127.0.0.1:5432/stockanalysis"
```

또는 docker container target:

```bash
export STOCKANALYSIS_PSQL_COMMAND="docker exec -i stockanalysis-ddl-verify psql -U postgres -d stockanalysis"
```

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-upsert \
  --series-id CPIAUCSL \
  --series-json tests/fixtures/fred_series_CPIAUCSL.json \
  --observations-json tests/fixtures/fred_observations_CPIAUCSL.json
```

출력에는 최소 아래가 포함된다.

- `run_id`
- `series_code`
- `observation_count`
- `skipped_count`

## Verification

현재 검증은 아래를 요구한다.

```bash
bash scripts/verify_macro_upsert_runner.sh
```

이 검증은:

- migration + seed 적용
- fixture 기반 `macro-upsert`
- `ops.pipeline_run` 상태 확인
- `macro.series`, `macro.observation` 적재 확인

를 수행한다.

## Current Limits

아직 구현하지 않은 것:

- live fetch smoke를 포함한 end-to-end 검증
- revision-aware ingest
- direct Python DB driver path
- scheduler/backfill orchestration
- multi-series batch execution

## Next Step

다음으로 자연스러운 확장:

1. `macro-batch-upsert`
2. `macro-run-history-report`
3. `sec-filings-ingest`
