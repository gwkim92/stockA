# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: sec-filing-raw-fetch
- 요청: SEC filing raw artifact fetch와 canonical update 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `sec-filing-raw-fetch` CLI가 `source_document`를 조회하고 raw artifact를 저장한 뒤 `raw_storage_uri`, `checksum`을 canonical DB에 반영한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: DB lookup, raw body fetch, local artifact write, canonical update, integration verify를 한 흐름으로 묶어야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - `sec_edgar` `source_document` row를 accession number로 조회한다.
  - fixture body가 있으면 deterministic path를 우선 사용한다.
  - live fetch가 필요하면 `source_document.url`과 SEC user-agent를 사용한다.
  - raw artifact는 repo-local artifact root 아래에 저장한다.
  - canonical DB에는 `raw_storage_uri`, `checksum`만 갱신한다.
- 핵심 tradeoff:
  - 새 artifact table을 미루는 대신 기존 `source_document` row update로 빠르게 raw path를 연다.
- 피해야 할 함정:
  - metadata lineage를 덮어쓰는 것
  - batch fetch와 event extraction을 한 task에 섞는 것
  - network smoke를 기본 검증에 강제하는 것

## Milestones

### Milestone 1

- 목표: raw fetch 모델, lookup, update 로직을 구현한다.
- 산출물: `sec/models.py`, `sec/sql.py`, `sec/raw_fetch.py`
- 검증: unit test로 lookup, artifact write, checksum update를 확인한다.

### Milestone 2

- 목표: CLI와 fixture 기반 integration verify를 연결한다.
- 산출물: `cli.py`, `tests/test_ingest_cli.py`, `scripts/verify_sec_filing_raw_fetch.sh`
- 검증: CLI summary test와 docker 기반 raw fetch verify가 통과한다.

### Milestone 3

- 목표: 운영 문서와 task artifact를 마무리한다.
- 산출물: `docs/sec-filing-raw-fetch.md`, task docs
- 검증: readiness 검증과 placeholder 검색이 통과한다.

## Dependencies

- 선행 조건:
  - `sec-filings-ingest` 완료
  - `source_document` canonical row 존재
  - docker 기반 verify 경로 존재
- 순서 제약:
  - metadata ingest 없이 raw fetch를 먼저 쓰지 않는다
  - batch fetch는 single-document path가 안정화된 뒤에만 확장한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 raw fetch 코드, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - raw fetch unit test 통과
  - CLI summary test 통과
  - docker 기반 raw artifact verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filing_raw_fetch.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filing-raw-fetch` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: `src/stockanalysis/ingest/sec/raw_fetch.py`, CLI 추가 명령, verify script, docs만 제거하면 이전 상태로 복귀한다.

## Open Questions

- 질문:
  - artifact 저장소를 계속 local file URI로 둘지 object storage URI로 일반화할지
- 임시 가정:
  - 현재는 deterministic verify와 local development를 위해 local file URI를 사용한다.
