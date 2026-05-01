# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: strategy-universe-slicing
- 요청: canonical universe와 price bars를 이용해 중장기 전략용 universe snapshot을 생성하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `strategy-universe-slice` CLI가 strategy-specific universe snapshot을 `signal` schema에 저장한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: schema, runner, CLI, tests, integration verify, AI role map 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - `signal.strategy_universe_batch/member`를 새로 둔다.
  - 후보는 active canonical instruments와 latest daily price availability로 자른다.
  - snapshot은 as-of date, strategy, horizon, universe version으로 재현 가능하게 저장한다.
- 핵심 tradeoff:
  - cycle/theme/AI ranking은 미루고, 가격 데이터가 있는 investable universe snapshot만 먼저 만든다.
- 피해야 할 함정:
  - canonical universe와 strategy universe를 같은 것으로 취급하는 것
  - LLM을 universe selection/ranking의 결정자로 섞는 것
  - snapshot identity 없이 멤버만 덮어쓰는 것

## Milestones

### Milestone 1

- 목표: schema와 task docs를 추가한다.
- 산출물: `0004_strategy_universe.sql`, task docs
- 검증: migration이 Docker Postgres에 적용된다.

### Milestone 2

- 목표: signal universe runner와 CLI를 구현한다.
- 산출물: `src/stockanalysis/signal/universe.py`, `src/stockanalysis/ingest/cli.py`, tests
- 검증: unit tests가 통과한다.

### Milestone 3

- 목표: integration verify와 AI role map을 마무리한다.
- 산출물: verify script, strategy universe doc, AI role map
- 검증: full Docker verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `market-universe-bootstrap` 완료
  - `market-price-universe-backfill` 완료
  - `market.daily_price_bar` populated
- 순서 제약:
  - strategy universe는 price data availability 이후에만 생성한다
  - recommendation은 strategy universe snapshot 이후에만 생성한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 schema, runner, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: migration/test 작성 후, docker verify 통과 후
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - migration verify 통과
  - unit tests 통과
  - docker 기반 strategy universe verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_strategy_universe_slicing.sh` 성공
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task strategy-universe-slicing` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: migration 0004, signal runner, CLI, verify script, docs만 제거하면 기존 market ingest 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 feature snapshot으로 갈지, theme enrichment로 갈지
- 임시 가정:
  - 현재는 deterministic price-availability universe slicing만 먼저 고정한다.
