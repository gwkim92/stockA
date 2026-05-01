# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: event-instrument-impact-bootstrap
- 요청: SEC events를 canonical instrument에 연결하는 bootstrap 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `event-instrument-impact-bootstrap` CLI가 pending SEC events를 찾아 canonical instrument lookup과 `event.event_instrument_impact` upsert를 수행한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: pending event discovery, canonical instrument lookup, pipeline run lifecycle, integration verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - pending SEC events를 조회한다.
  - event title/summary에서 company name을 추출한다.
  - canonical issuer/instrument exact-match lookup을 수행한다.
  - event type별 deterministic 기본 impact와 함께 `event.event_instrument_impact`를 적재한다.
  - bootstrap run summary를 반환한다.
- 핵심 tradeoff:
  - fuzzy match와 symbol master를 미루는 대신 deterministic exact match만 먼저 연다.
- 피해야 할 함정:
  - fuzzy matching으로 잘못된 instrument에 연결하는 것
  - 이미 impact가 있는 이벤트를 반복 처리하는 것
  - classification bootstrap과 instrument bootstrap을 다시 섞는 것

## Milestones

### Milestone 1

- 목표: candidate/sql/helper를 구현한다.
- 산출물: `sec/models.py`, `sec/sql.py`, `tests/test_sec_instrument_impact.py`
- 검증: unit test로 pending candidates, instrument lookup SQL, impact upsert SQL을 확인한다.

### Milestone 2

- 목표: bootstrap runner와 CLI를 연결한다.
- 산출물: `sec/instrument_impact.py`, `cli.py`, `tests/test_ingest_cli.py`
- 검증: runner summary test와 CLI summary test가 통과한다.

### Milestone 3

- 목표: integration verify와 운영 문서를 마무리한다.
- 산출물: `verify_event_instrument_impact_bootstrap.sh`, `docs/event-instrument-impact-bootstrap.md`, task docs
- 검증: docker 기반 instrument impact verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `sec-filings-event-batch-extract` 완료
  - `event.event` rows 존재
  - canonical `ref.issuer`, `ref.instrument` schema 존재
- 순서 제약:
  - event row 없이 instrument impact를 먼저 만들지 않는다
  - broader issuer master 작업은 instrument bootstrap 후에만 확장한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 bootstrap code, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - instrument impact unit test 통과
  - CLI summary test 통과
  - docker 기반 instrument bootstrap verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-instrument-impact-bootstrap` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: instrument bootstrap code, CLI, verify script, docs만 제거하면 기존 SEC event pipeline 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 `sec-companyfacts-ingest`와 retry policy 중 어디에 둘지
- 임시 가정:
  - 현재는 canonical instrument linkage만 먼저 고정한다.
