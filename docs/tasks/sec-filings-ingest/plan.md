# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: sec-filings-ingest
- 요청: SEC filing 메타데이터를 canonical DB에 적재하는 ingest 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `sec-filings-upsert` CLI가 submissions payload를 읽어 `ingest.source_document`에 filing metadata를 upsert하고 run history를 남긴다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 비정형 payload 정규화, archive URL 생성, source_document 매핑, integration verify, 문서를 함께 고정해야 한다.

## Architecture Or Approach

- 접근 방식:
  - 기존 SEC source adapter는 그대로 사용한다.
  - submissions payload에서 recent filings arrays만 정규화한다.
  - metadata만 `source_document`에 upsert하고 raw filing body는 다루지 않는다.
- 핵심 tradeoff:
  - body/raw artifact를 미루는 대신 빠르게 canonical document metadata를 확보한다.
- 피해야 할 함정:
  - issuer/instrument mapping까지 한 번에 끌어오는 것
  - archive URL 규칙을 임의로 추정하고 검증하지 않는 것
  - metadata와 event extraction을 한 task에 섞는 것

## Milestones

### Milestone 1

- 목표: submissions 정규화와 SQL renderer를 구현한다.
- 산출물: `sec/models.py`, `sec/submissions.py`, `sec/sql.py`
- 검증: unit test로 filing record와 SQL output을 확인한다.

### Milestone 2

- 목표: upsert runner와 CLI를 연결한다.
- 산출물: `sec/upsert.py`, `cli.py`
- 검증: CLI summary test와 runner lifecycle test가 통과한다.

### Milestone 3

- 목표: integration verify와 문서를 마무리한다.
- 산출물: `verify_sec_filings_ingest.sh`, `docs/sec-filings-ingest.md`, task docs
- 검증: docker 기반 source_document upsert와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `ingest-bootstrap` 완료
  - `macro` ingest chain 완료
  - docker 기반 verify 경로 존재
- 순서 제약:
  - filings 정규화 없이 source_document upsert를 먼저 쓰지 않는다
  - metadata mapping을 고정하기 전 raw artifact 저장을 섞지 않는다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 SEC normalize, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, integration verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - SEC normalize unit test 통과
  - CLI summary test 통과
  - docker 기반 source_document ingest 검증 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_filings_ingest.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-ingest` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: `src/stockanalysis/ingest/sec/`, CLI 추가 명령, verify script, docs만 제거하면 이전 상태로 복귀한다.

## Open Questions

- 질문:
  - `source_document.summary`에 filing metadata를 얼마나 많이 담을지
- 임시 가정:
  - 현재는 form, company, items, file number 정도의 간단한 텍스트 요약만 넣는다.
