# Macro Ingest

## Goal

이 문서는 첫 실제 적재 경로로 `FRED -> normalize -> macro upsert SQL` 흐름을 정의한다.

현재 구현 범위:

- 기본 매크로 series 목록
- FRED series metadata/observations 정규화
- fixture 기반 end-to-end 검증
- `macro.series`, `macro.observation`용 SQL upsert 생성

## Why Macro First

거시지표는 종목 유니버스보다 먼저 붙이기 쉽다.

- 종목 mapping이 필요 없다
- 구조가 단순하다
- 시장 레짐과 테마 사이클 입력으로 바로 쓸 수 있다

그래서 첫 실제 ingest는 `FRED` 기반 macro가 적합하다.

## Default Series

초기 기본 시리즈:

- `FEDFUNDS`
- `CPIAUCSL`
- `PCEPI`
- `UNRATE`
- `DGS10`
- `DGS2`
- `T10Y2Y`
- `GDPC1`

이 목록은 bootstrap 세트다.
이후 정책, 성장, 유동성 관련 series를 더 늘릴 수 있다.

## Current Flow

1. FRED `series` endpoint에서 metadata를 읽는다.
2. FRED `series/observations` endpoint에서 observation을 읽는다.
3. `.` 값은 missing으로 간주하고 skip한다.
4. 정규화된 결과를 `MacroSyncResult`로 만든다.
5. 필요 시 `macro.series`와 `macro.observation` upsert SQL을 생성한다.

## Current Implementation Boundary

현재 구현한 것:

- fixture 파일을 이용한 deterministic 검증
- FRED live fetch entrypoint
- SQL upsert 문자열 생성

아직 구현하지 않은 것:

- Postgres direct execute/upsert
- pipeline run 연결
- ALFRED revision/vintage 처리
- scheduler/backfill state

## CLI

지원 명령:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-default-series
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-sync \
  --series-id CPIAUCSL \
  --series-json tests/fixtures/fred_series_CPIAUCSL.json \
  --observations-json tests/fixtures/fred_observations_CPIAUCSL.json \
  --sql-output /tmp/cpiaucl.sql
```

live fetch 예시:

```bash
export STOCKANALYSIS_FRED_API_KEY=...
PYTHONPATH=src python3 -m stockanalysis.ingest.cli macro-sync \
  --series-id CPIAUCSL \
  --observation-start 2020-01-01
```

## Verification

현재 검증은 아래 명령으로 한다.

```bash
bash scripts/verify_macro_ingest.sh
```

이 명령은:

- compileall
- 전체 unittest
- `macro-default-series`
- fixture 기반 `macro-sync`

를 검증한다.

## Next Step

이후 자연스러운 확장:

1. `macro-upsert-runner`
2. `sec-filings-ingest`
3. `market-data-ingest`
4. `universe-bootstrap`
