# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: sec-filings-event-batch-extract
- 요청: pending SEC raw filing을 batch로 event화하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `sec-filings-event-batch-extract` CLI가 pending 문서를 찾아 `sec-filings-event-extract`를 문서별로 실행하고 success/failure summary를 반환한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: pending discovery SQL, batch orchestration, integration verify, 운영 문서를 한 흐름으로 묶어야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - explicit accession list가 있으면 그것을 우선 처리한다.
  - 없으면 `raw_storage_uri`가 있고 아직 `source` event link가 없는 SEC 문서를 조회한다.
  - 문서마다 기존 single-document extractor를 호출한다.
  - summary JSON에 success/failure를 집계한다.
- 핵심 tradeoff:
  - batch parent pipeline을 미루는 대신 간단한 discovery + orchestration layer로 빠르게 연다.
- 피해야 할 함정:
  - batch 자체에 별도 event semantics를 섞는 것
  - pending discovery와 retry policy를 한 task에 섞는 것
  - 이미 source link가 있는 문서를 반복 처리하는 것

## Milestones

### Milestone 1

- 목표: pending discovery SQL과 batch runner를 구현한다.
- 산출물: `sec/sql.py`, `sec/event_extract.py`, `tests/test_sec_event_extract.py`
- 검증: unit test로 pending ids와 continue-on-error behavior를 확인한다.

### Milestone 2

- 목표: CLI와 2-document integration verify를 연결한다.
- 산출물: `cli.py`, `tests/test_ingest_cli.py`, `tests/fixtures/sec_filing_aapl_20240629_10q.html`, `verify_sec_filings_event_batch_extract.sh`
- 검증: CLI summary test와 docker 기반 2-document batch verify가 통과한다.

### Milestone 3

- 목표: 운영 문서와 task artifact를 마무리한다.
- 산출물: `docs/sec-filings-event-batch-extract.md`, task docs
- 검증: readiness 검증과 placeholder 검색이 통과한다.

## Dependencies

- 선행 조건:
  - `sec-filings-event-extraction` 완료
  - `sec-filing-raw-fetch` 완료
  - docker 기반 verify 경로 존재
- 순서 제약:
  - raw artifact가 없는 문서를 batch 대상에 포함하지 않는다
  - impact mapping은 batch extraction이 안정화된 뒤에만 확장한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 batch code, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - pending discovery unit test 통과
  - CLI summary test 통과
  - docker 기반 2-document batch verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_batch_extract.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-batch-extract` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: batch CLI와 pending discovery 코드, verify script, docs만 제거하면 single-document extraction 상태로 복귀한다.

## Open Questions

- 질문:
  - parent batch run과 retry queue를 언제 도입할지
- 임시 가정:
  - 현재는 per-document run만 남기고 batch 자체는 summary JSON만 반환한다.
