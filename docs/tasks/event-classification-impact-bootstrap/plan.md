# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: event-classification-impact-bootstrap
- 요청: SEC events를 minimal classification taxonomy에 연결하는 bootstrap 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `event-classification-impact-bootstrap` CLI가 pending SEC events를 찾아 classification nodes/edges를 bootstrap하고 `event.event_classification_impact`를 upsert한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: taxonomy bootstrap, pending event discovery, impact upsert, integration verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - pending SEC events를 조회한다.
  - minimal reporting taxonomy를 한 번 bootstrap한다.
  - event type별 deterministic node mapping으로 classification impacts를 적재한다.
  - bootstrap run summary를 반환한다.
- 핵심 tradeoff:
  - richer taxonomy와 semantic mapping을 미루는 대신 minimal internal reporting themes만 먼저 연다.
- 피해야 할 함정:
  - sector/theme taxonomy 전체를 한 task에 다 넣는 것
  - event extraction과 impact mapping을 다시 섞는 것
  - 이미 impact가 있는 이벤트를 반복 처리하는 것

## Milestones

### Milestone 1

- 목표: candidate/sql/bootstrap helper를 구현한다.
- 산출물: `sec/models.py`, `sec/sql.py`, `tests/test_sec_classification_impact.py`
- 검증: unit test로 pending candidates, taxonomy bootstrap SQL, impact upsert SQL을 확인한다.

### Milestone 2

- 목표: bootstrap runner와 CLI를 연결한다.
- 산출물: `sec/classification_impact.py`, `cli.py`, `tests/test_ingest_cli.py`
- 검증: runner summary test와 CLI summary test가 통과한다.

### Milestone 3

- 목표: integration verify와 운영 문서를 마무리한다.
- 산출물: `verify_event_classification_impact_bootstrap.sh`, `docs/event-classification-impact-bootstrap.md`, task docs
- 검증: docker 기반 taxonomy/bootstrap verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `sec-filings-event-batch-extract` 완료
  - `event.event` rows 존재
  - docker 기반 verify 경로 존재
- 순서 제약:
  - event row 없이 classification impact를 먼저 만들지 않는다
  - richer instrument impact는 classification impact bootstrap 후에만 확장한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 bootstrap code, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - classification impact unit test 통과
  - CLI summary test 통과
  - docker 기반 taxonomy/bootstrap verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_event_classification_impact_bootstrap.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-classification-impact-bootstrap` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: classification impact bootstrap code, CLI, verify script, docs만 제거하면 기존 event pipeline 상태로 복귀한다.

## Open Questions

- 질문:
  - 다음 우선순위를 instrument impact bootstrap과 retry policy 중 어디에 둘지
- 임시 가정:
  - 현재는 event -> classification node 연결만 먼저 고정한다.
