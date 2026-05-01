# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: market-universe-bootstrap
- 요청: `SEC company_tickers_exchange.json` 기반 미국 상장 universe를 canonical reference tables에 bootstrap하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-universe-bootstrap` CLI가 SEC ticker/exchange payload를 읽어 supported exchange만 선별하고 `ref.issuer`, `ref.instrument`에 upsert한 뒤 summary를 반환한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: 단일 종목 가격 적재를 넘어 실제 투자 대상 universe를 canonical reference layer에 올려야 batch market/SEC ingest와 이후 thesis/recommendation 단계가 이어진다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/market/price.py`
- 관련 문서:
  - `docs/market-price-batch-ingest.md`
  - `docs/verification-plan.md`
  - `docs/tasks/market-price-batch-ingest/handoff.md`
- 이전 결정:
  - 초기 미국 market reference seed는 `XNAS`, `XNYS`, `ARCX`만 존재한다.
  - SEC filing/companyfacts mapping은 canonical issuer/company exact match를 우선한다.
  - 이번 단계는 exchange-supported listed universe bootstrap만 다루고 delisting propagation은 미룬다.

## Scope

- 포함:
  - `sec` source adapter에 `company_tickers_exchange` dataset 추가
  - SEC payload normalization
  - `Nasdaq`, `NYSE` exchange mapping
  - canonical `ref.issuer`, `ref.instrument` upsert
  - CLI, tests, fixture, integration verify, task docs
- 제외:
  - delisted universe 관리
  - `OTC`, `CBOE` 지원
  - ETF/common stock 세부 타입 구분
  - universe version table 도입

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/plans/2026-04-23-market-universe-bootstrap.md`
  - `docs/market-universe-bootstrap.md`
  - `docs/tasks/market-price-batch-ingest/handoff.md`
  - `docs/tasks/market-universe-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_market_universe_bootstrap.sh`
  - `src/stockanalysis/ingest/sources/sec.py`
  - `src/stockanalysis/ingest/market/universe.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_market_universe.py`
  - `tests/test_ingest_cli.py`
  - `tests/fixtures/sec_company_tickers_exchange_sample.json`
- 수정 금지 파일:
  - migrations and seeds
  - macro ingest code
  - existing SEC event extraction code
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-universe-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `docs/market-universe-bootstrap.md`
  - `docs/tasks/market-universe-bootstrap/contract.md`
  - `docs/tasks/market-universe-bootstrap/plan.md`
  - `docs/tasks/market-universe-bootstrap/handoff.md`
  - `scripts/verify_market_universe_bootstrap.sh`
  - `src/stockanalysis/ingest/market/universe.py`
  - `tests/test_market_universe.py`
  - `tests/fixtures/sec_company_tickers_exchange_sample.json`
- 선택 결과물:
  - `docs/tasks/market-universe-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] fixture 기반 universe bootstrap이 실제로 동작한다
- [x] supported exchange filter가 문서와 코드에서 일치한다

## Verification Plan

- 자동 검증: `bash scripts/verify_market_universe_bootstrap.sh`, `awh verify --task market-universe-bootstrap`, placeholder 검색
- 수동 검증: `docs/market-universe-bootstrap.md`가 SEC source, exchange mapping, current limitations를 분명히 설명하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, canonical issuer/instrument rows 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `market-universe-bootstrap` command와 universe runner 코드만 제거하면 기존 market price/SEC ingest는 유지된다.

## Open Questions

- 질문: 초기 universe를 전체 SEC listed set으로 둘지, 이후 curated large-cap subset을 별도 version으로 둘지
- 답이 없을 때 적용할 임시 가정: 현재는 SEC listed set 중 supported exchange만 canonical bootstrap한다.
