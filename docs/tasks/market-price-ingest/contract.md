# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: market-price-ingest
- 요청: Alpha Vantage daily adjusted price JSON을 canonical `market.daily_price_bar`에 적재하는 첫 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-price-upsert` CLI가 selected daily price bars를 canonical instrument에 연결하고 `market.daily_price_bar`를 upsert한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: cycle, recommendation, review 엔진이 모두 가격 시계열을 필요로 하므로 canonical daily bar 적재는 필수 baseline이다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/sources/alpha_vantage.py`
  - `db/migrations/0002_priority_1_tables.sql`
- 관련 문서:
  - `docs/ingest-bootstrap.md`
  - `docs/sec-companyfacts-ingest.md`
  - `docs/verification-plan.md`
  - `docs/tasks/sec-companyfacts-ingest/handoff.md`
- 이전 결정:
  - bootstrap market source는 Alpha Vantage를 사용한다.
  - canonical instrument linkage는 exact-match lookup을 우선한다.
  - first-step price ingest는 daily adjusted bars만 다룬다.

## Scope

- 포함:
  - Alpha Vantage daily adjusted payload normalize
  - exact-match canonical instrument lookup
  - `market.daily_price_bar` upsert
  - CLI, tests, integration verify, task docs
- 제외:
  - intraday data
  - splits/dividends 별도 테이블 적재
  - multi-symbol batch orchestration
  - turnover/market cap enrichment

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-20-market-price-ingest.md`
  - `docs/market-price-ingest.md`
  - `docs/tasks/sec-companyfacts-ingest/handoff.md`
  - `docs/tasks/market-price-ingest/`
  - `docs/verification-plan.md`
  - `scripts/verify_market_price_ingest.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/market/`
  - `tests/test_ingest_cli.py`
  - `tests/test_market_price.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_ingest.sh`
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `src/stockanalysis/ingest/market/price.py`
  - `tests/test_market_price.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json`
  - `scripts/verify_market_price_ingest.sh`
  - `docs/market-price-ingest.md`
  - `docs/tasks/market-price-ingest/contract.md`
  - `docs/tasks/market-price-ingest/plan.md`
  - `docs/tasks/market-price-ingest/handoff.md`
- 선택 결과물:
  - `docs/tasks/market-price-ingest/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] selected daily bars가 canonical daily price table에 적재된다
- [x] fixture 기반 market price integration verify 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_market_price_ingest.sh`, `awh verify --task market-price-ingest`, placeholder 검색
- 수동 검증: `docs/market-price-ingest.md`가 source, mapping, current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, daily bar row 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `market-price-upsert` command와 price ingest 코드만 제거하면 기존 macro/SEC pipeline은 유지된다.

## Open Questions

- 질문: first price ingest 이후 batch universe path를 어떤 우선순위로 확장할지
- 답이 없을 때 적용할 임시 가정: 현재는 single-symbol daily adjusted path만 먼저 고정한다.
