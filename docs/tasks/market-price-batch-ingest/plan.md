# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: market-price-batch-ingest
- 요청: 여러 symbol의 daily adjusted payload를 canonical daily bar table에 batch 적재하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `market-price-batch-upsert` CLI가 여러 symbol을 순차 처리하고 aggregate summary를 반환한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: batch wrapper, fixture directory resolution, continue-on-error summary, integration verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - existing `run_market_price_upsert`를 per-symbol worker로 재사용한다.
  - batch wrapper가 symbol list와 fixture directory resolution만 추가한다.
  - batch는 per-symbol success/failure summary와 total bar count를 반환한다.
- 핵심 tradeoff:
  - parent batch pipeline run과 rate limiting을 미루는 대신 deterministic wrapper만 먼저 연다.
- 피해야 할 함정:
  - single-symbol runner 로직을 중복 구현하는 것
  - fixture file naming contract를 불명확하게 두는 것
  - batch failure가 전체를 즉시 중단하게 만드는 것

## Milestones

### Milestone 1

- 목표: batch runner와 fixture resolution을 구현한다.
- 산출물: `market/price.py`, `tests/test_market_price.py`
- 검증: unit test로 batch success/failure와 fixture directory resolution을 확인한다.

### Milestone 2

- 목표: batch CLI를 연결한다.
- 산출물: `cli.py`, `tests/test_ingest_cli.py`
- 검증: batch CLI summary test가 통과한다.

### Milestone 3

- 목표: second fixture, docker verify, 운영 문서를 마무리한다.
- 산출물: `alpha_vantage_daily_adjusted_MSFT.json`, `verify_market_price_batch_ingest.sh`, `docs/market-price-batch-ingest.md`, task docs
- 검증: docker 기반 2-symbol batch verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `market-price-ingest` 완료
  - canonical `daily_price_bar` schema 존재
  - Apple fixture 기반 single-symbol verify 존재
- 순서 제약:
  - batch path는 single-symbol runner를 재사용한다
  - default universe 확장은 batch wrapper 검증 후에만 한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 batch code, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - batch unit test 통과
  - batch CLI summary test 통과
  - docker 기반 batch verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_batch_ingest.sh` 성공
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-batch-ingest` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: batch wrapper, CLI, verify script, docs만 제거하면 기존 single-symbol ingest 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 default universe bootstrap과 retry policy 중 어디에 둘지
- 임시 가정:
  - 현재는 explicit symbol list 기반 batch만 먼저 고정한다.
