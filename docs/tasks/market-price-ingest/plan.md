# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: market-price-ingest
- 요청: Alpha Vantage daily adjusted를 canonical daily bar schema에 연결하는 ingest 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `market-price-upsert` CLI가 selected daily bars를 normalized bar rows로 적재한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: payload normalize, canonical instrument lookup, daily bar upsert, integration verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - Alpha Vantage daily adjusted payload를 읽는다.
  - symbol 기준으로 canonical instrument exact-match lookup을 수행한다.
  - normalized daily bars를 `market.daily_price_bar`에 upsert한다.
  - pipeline run summary를 반환한다.
- 핵심 tradeoff:
  - batch universe와 richer market metadata를 미루는 대신 single-symbol daily path만 먼저 연다.
- 피해야 할 함정:
  - adjusted close semantics를 일반 close와 섞는 것
  - fuzzy symbol lookup으로 잘못된 instrument에 연결하는 것
  - turnover/market cap을 가짜 값으로 채우는 것

## Milestones

### Milestone 1

- 목표: market price normalize와 SQL renderer를 구현한다.
- 산출물: `market/price.py`, `tests/test_market_price.py`
- 검증: unit test로 Alpha Vantage normalize, symbol lookup, daily bar upsert SQL을 확인한다.

### Milestone 2

- 목표: runner와 CLI를 연결한다.
- 산출물: `cli.py`, `tests/test_ingest_cli.py`
- 검증: runner summary test와 CLI summary test가 통과한다.

### Milestone 3

- 목표: integration verify와 운영 문서를 마무리한다.
- 산출물: `tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json`, `verify_market_price_ingest.sh`, `docs/market-price-ingest.md`, task docs
- 검증: docker 기반 market price ingest verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `ingest-bootstrap` 완료
  - `sec-companyfacts-ingest` 완료
  - canonical `daily_price_bar` schema 존재
- 순서 제약:
  - canonical instrument row 없이 price upsert를 완료라고 보지 않는다
  - batch universe ingest는 single-symbol baseline 검증 후에만 한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 normalize code, SQL, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - market price unit test 통과
  - CLI summary test 통과
  - docker 기반 market price ingest verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_ingest.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-ingest` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: market price ingest code, CLI, verify script, docs만 제거하면 기존 pipeline 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 universe batch ingest와 retry policy 중 어디에 둘지
- 임시 가정:
  - 현재는 single-symbol daily adjusted ingest만 먼저 고정한다.
