# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: market-universe-bootstrap
- 요청: `SEC company_tickers_exchange.json` 기반 미국 상장 universe를 canonical reference tables에 bootstrap하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `market-universe-bootstrap` CLI가 SEC payload를 읽어 supported exchange의 issuer/instrument rows를 canonical reference layer에 올린다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: source adapter, normalization, SQL upsert, CLI, fixture, docker verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - `sec` source adapter에 `company_tickers_exchange` dataset을 추가한다.
  - market universe runner가 payload를 정규화하고 supported exchange만 필터링한다.
  - canonical upsert는 distinct issuer insert 뒤 instrument upsert 순서로 수행한다.
- 핵심 tradeoff:
  - delisting과 security type 세분화를 미루는 대신 exact name + symbol bootstrap path만 먼저 연다.
- 피해야 할 함정:
  - unsupported exchange rows를 암묵적으로 잘못 매핑하는 것
  - issuer 중복 row를 불필요하게 양산하는 것
  - SEC exact company name을 중간에 임의 정규화해서 이후 SEC companyfacts lookup을 깨는 것

## Milestones

### Milestone 1

- 목표: source adapter와 normalization/unit test를 구현한다.
- 산출물: `sources/sec.py`, `market/universe.py`, `tests/test_market_universe.py`
- 검증: normalization/filter/upsert summary unit test가 통과한다.

### Milestone 2

- 목표: CLI와 fixture를 연결한다.
- 산출물: `cli.py`, `test_ingest_cli.py`, sample fixture
- 검증: CLI summary test가 통과한다.

### Milestone 3

- 목표: docker verify와 운영 문서를 마무리한다.
- 산출물: `verify_market_universe_bootstrap.sh`, `docs/market-universe-bootstrap.md`, task docs
- 검증: docker 기반 universe bootstrap verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `market-price-batch-ingest` 완료
  - canonical `ref.market`, `ref.exchange`, `ref.issuer`, `ref.instrument` schema 존재
  - SEC source adapter와 user-agent runtime contract 존재
- 순서 제약:
  - universe bootstrap은 supported exchange mapping이 고정된 뒤에만 진행한다
  - curated watchlist/strategy universe는 canonical bootstrap 이후에만 설계한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 source adapter, runner, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - normalization/filter unit test 통과
  - CLI summary test 통과
  - docker 기반 universe bootstrap verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh` 성공
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-universe-bootstrap` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: source dataset addition, universe runner, CLI, verify script, docs만 제거하면 기존 ingest 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 curated universe slicing으로 갈지, price batch backfill 자동화로 갈지
- 임시 가정:
  - 현재는 canonical bootstrap만 먼저 고정하고 strategy-specific universe slicing은 후속 task로 분리한다.
