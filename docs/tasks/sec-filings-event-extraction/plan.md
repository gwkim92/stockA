# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: sec-filings-event-extraction
- 요청: raw SEC filing artifact에서 heuristic event를 추출해 canonical event tables에 적재한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `sec-filings-event-extract` CLI가 raw SEC filing을 읽고 `event.event`, `event.event_document_link`를 upsert한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: raw artifact 로딩, form mapping, SQL upsert, integration verify, 운영 문서를 한 흐름으로 묶어야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - accession number로 `source_document`를 조회한다.
  - `raw_storage_uri` local file URI에서 본문을 읽는다.
  - form type과 본문 excerpt로 heuristic event candidate를 만든다.
  - dedupe key 기준으로 `event.event`를 upsert하고 `event.event_document_link`를 연결한다.
- 핵심 tradeoff:
  - LLM과 impact mapping을 미루는 대신 deterministic event skeleton을 빠르게 연다.
- 피해야 할 함정:
  - semantic extraction과 batch orchestration을 한 task에 섞는 것
  - raw artifact가 없는 문서를 강제로 처리하는 것
  - dedupe key 없이 event row를 중복 생성하는 것

## Milestones

### Milestone 1

- 목표: event candidate와 SQL renderer를 구현한다.
- 산출물: `sec/models.py`, `sec/sql.py`, `tests/test_sec_event_extract.py`
- 검증: unit test로 candidate mapping과 SQL output을 확인한다.

### Milestone 2

- 목표: runner와 CLI를 연결한다.
- 산출물: `sec/event_extract.py`, `cli.py`, `tests/test_ingest_cli.py`
- 검증: pipeline run lifecycle test와 CLI summary test가 통과한다.

### Milestone 3

- 목표: integration verify와 운영 문서를 마무리한다.
- 산출물: `verify_sec_filings_event_extract.sh`, `docs/sec-filings-event-extraction.md`, task docs
- 검증: docker 기반 event extraction verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `sec-filings-ingest` 완료
  - `sec-filing-raw-fetch` 완료
  - docker 기반 verify 경로 존재
- 순서 제약:
  - raw artifact 없이 event extraction을 먼저 쓰지 않는다
  - impact mapping은 event row가 안정화된 뒤에만 확장한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 event extraction 코드, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - event candidate unit test 통과
  - CLI summary test 통과
  - docker 기반 event extraction verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-extraction` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: `src/stockanalysis/ingest/sec/event_extract.py`, CLI 추가 명령, verify script, docs만 제거하면 이전 상태로 복귀한다.

## Open Questions

- 질문:
  - 다음 우선순위를 batch extraction과 classification impact bootstrap 중 어디에 둘지
- 임시 가정:
  - 현재는 single-document event extraction path를 먼저 안정화한다.
