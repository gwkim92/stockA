# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: market-price-universe-backfill
- 요청: canonical active universe에서 symbol list를 읽어 batch price ingest를 자동화하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `market-price-universe-backfill` CLI가 canonical universe selection과 existing batch price runner를 연결한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: symbol selection SQL, batch reuse, CLI, new fixture, docker verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - canonical active instrument query는 `ref.instrument` + `ref.exchange` 기준으로 수행한다.
  - selection 결과 symbol list를 existing `run_market_price_batch_upsert`에 그대로 넘긴다.
  - explicit symbol batch path는 유지하고, universe backfill은 orchestration layer만 추가한다.
- 핵심 tradeoff:
  - parent backfill run abstraction은 미루는 대신 canonical selection + existing batch reuse만 먼저 연다.
- 피해야 할 함정:
  - canonical selection과 explicit symbol batch 로직을 중복 구현하는 것
  - unsupported exchange filter를 universe bootstrap과 다르게 해석하는 것
  - no-op backfill을 조용히 성공시키는 것

## Milestones

### Milestone 1

- 목표: canonical symbol selection과 unit test를 구현한다.
- 산출물: `market/backfill.py`, `tests/test_market_backfill.py`
- 검증: selection SQL와 backfill summary unit test가 통과한다.

### Milestone 2

- 목표: CLI와 fixture를 연결한다.
- 산출물: `cli.py`, `test_ingest_cli.py`, `alpha_vantage_daily_adjusted_BABA.json`
- 검증: CLI summary test가 통과한다.

### Milestone 3

- 목표: docker verify와 운영 문서를 마무리한다.
- 산출물: `verify_market_price_universe_backfill.sh`, `docs/market-price-universe-backfill.md`, task docs
- 검증: market universe bootstrap 후 universe backfill verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `market-universe-bootstrap` 완료
  - `market-price-batch-ingest` 완료
  - canonical `ref.instrument`와 `market.daily_price_bar` schema 존재
- 순서 제약:
  - universe-driven backfill은 canonical universe bootstrap 이후에만 가능하다
  - curated strategy slicing은 universe-driven backfill 이후에만 다룬다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 selection runner, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - selection/backfill unit test 통과
  - CLI summary test 통과
  - docker 기반 universe backfill verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh` 성공
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-universe-backfill` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: backfill runner, CLI, fixture, verify script, docs만 제거하면 기존 batch ingest 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 live SEC smoke로 갈지, strategy universe slicing으로 갈지
- 임시 가정:
  - 현재는 fixture 기반 deterministic universe backfill만 먼저 고정한다.
