# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: market-price-universe-backfill
- 요청: canonical active universe에서 symbol list를 읽어 batch price ingest를 자동화하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-price-universe-backfill` CLI가 canonical `ref.instrument`에서 active symbol list를 읽고 기존 batch price ingest runner를 재사용해 `market.daily_price_bar`를 적재한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 현재 batch price ingest는 caller가 symbol list를 직접 넘겨야 한다. universe bootstrap 이후에는 canonical reference layer가 이미 있으므로, 다음 단계는 universe-driven backfill 자동화가 맞다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/market/universe.py`
  - `src/stockanalysis/ingest/cli.py`
- 관련 문서:
  - `docs/market-universe-bootstrap.md`
  - `docs/market-price-batch-ingest.md`
  - `docs/verification-plan.md`
- 이전 결정:
  - canonical universe bootstrap은 `Nasdaq`, `NYSE`만 지원한다.
  - price batch ingest는 existing `run_market_price_upsert` per-symbol runner를 재사용한다.
  - current reference seed exchange는 `XNAS`, `XNYS`, `ARCX`다.

## Scope

- 포함:
  - canonical active symbol lookup
  - optional exchange filter와 limit
  - existing market price batch runner reuse
  - CLI, tests, fixture, docker verify, task docs
- 제외:
  - scheduling/retry policy
  - rate limiting/backoff
  - dynamic universe versioning
  - turnover/market cap enrichment

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-23-market-price-universe-backfill.md`
  - `docs/market-price-universe-backfill.md`
  - `docs/tasks/market-universe-bootstrap/handoff.md`
  - `docs/tasks/market-price-universe-backfill/`
  - `docs/verification-plan.md`
  - `scripts/verify_market_price_universe_backfill.sh`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_backfill.py`
  - `tests/test_ingest_cli.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_BABA.json`
- 수정 금지 파일:
  - migrations and seeds
  - SEC event extraction code
  - market universe bootstrap logic
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-universe-backfill`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `docs/market-price-universe-backfill.md`
  - `docs/tasks/market-price-universe-backfill/contract.md`
  - `docs/tasks/market-price-universe-backfill/plan.md`
  - `docs/tasks/market-price-universe-backfill/handoff.md`
  - `scripts/verify_market_price_universe_backfill.sh`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `tests/test_market_backfill.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_BABA.json`
- 선택 결과물:
  - `docs/tasks/market-price-universe-backfill/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] canonical universe에서 symbol list를 읽는 backfill path가 실제로 동작한다
- [x] fixture 기반 universe backfill integration verify가 존재한다

## Verification Plan

- 자동 검증: `bash scripts/verify_market_price_universe_backfill.sh`, `awh verify --task market-price-universe-backfill`, placeholder 검색
- 수동 검증: `docs/market-price-universe-backfill.md`가 selection rule과 current limits를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, canonical universe 기반 per-symbol bar rows 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `market-price-universe-backfill` command와 backfill runner 코드만 제거하면 기존 explicit symbol batch ingest는 유지된다.

## Open Questions

- 질문: 이후 curated strategy universe를 `classification`/`signal` 계층과 어떻게 연결할지
- 답이 없을 때 적용할 임시 가정: 현재는 canonical active universe 전체 또는 제한된 exchange subset만 backfill 대상으로 사용한다.
