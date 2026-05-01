# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: market-price-batch-ingest
- 요청: 여러 종목의 Alpha Vantage daily adjusted payload를 canonical daily bar table에 batch 적재하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-price-batch-upsert` CLI가 여러 symbol을 받아 canonical instrument lookup과 `market.daily_price_bar` upsert를 순차 실행하고 aggregate summary를 반환한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 실제 유니버스 적재는 단일 종목이 아니라 여러 종목을 한 번에 처리해야 하므로, batch orchestration이 있어야 본격적인 시장 데이터 backfill로 넘어갈 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
- 관련 문서:
  - `docs/market-price-ingest.md`
  - `docs/verification-plan.md`
  - `docs/tasks/market-price-ingest/handoff.md`
- 이전 결정:
  - single-symbol market price ingest는 구현 완료 상태다.
  - canonical instrument linkage는 primary symbol exact match를 우선한다.
  - first batch path는 repeatable symbol list와 fixture directory mode만 다룬다.

## Scope

- 포함:
  - repeatable symbol list 처리
  - fixture directory resolution
  - per-symbol existing runner 재사용
  - batch summary와 CLI, tests, integration verify, task docs
- 제외:
  - default universe discovery
  - rate limiting/backoff
  - parent batch pipeline run
  - live Alpha Vantage smoke

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-23-market-price-batch-ingest.md`
  - `docs/market-price-batch-ingest.md`
  - `docs/tasks/market-price-ingest/handoff.md`
  - `docs/tasks/market-price-batch-ingest/`
  - `docs/verification-plan.md`
  - `scripts/verify_market_price_batch_ingest.sh`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_price.py`
  - `tests/test_ingest_cli.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_MSFT.json`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_batch_ingest.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-batch-ingest`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `docs/market-price-batch-ingest.md`
  - `docs/tasks/market-price-batch-ingest/contract.md`
  - `docs/tasks/market-price-batch-ingest/plan.md`
  - `docs/tasks/market-price-batch-ingest/handoff.md`
  - `scripts/verify_market_price_batch_ingest.sh`
  - `tests/fixtures/alpha_vantage_daily_adjusted_MSFT.json`
- 선택 결과물:
  - `docs/tasks/market-price-batch-ingest/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] 2-symbol batch upsert가 실제로 동작한다
- [x] fixture 기반 batch integration verify 경로가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_market_price_batch_ingest.sh`, `awh verify --task market-price-batch-ingest`, placeholder 검색
- 수동 검증: `docs/market-price-batch-ingest.md`가 batch summary shape와 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, 2-symbol bar rows 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `market-price-batch-upsert` command와 batch wrapper 코드만 제거하면 single-symbol price ingest는 유지된다.

## Open Questions

- 질문: batch 이후 default universe bootstrap을 어떤 기준으로 고정할지
- 답이 없을 때 적용할 임시 가정: 현재는 caller가 symbol list를 직접 넘긴다.
