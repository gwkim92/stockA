# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: sec-companyfacts-ingest
- 요청: SEC companyfacts를 canonical financial schema에 연결하는 ingest 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-20

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `sec-companyfacts-upsert` CLI가 selected SEC companyfacts facts를 normalized period/value rows로 적재한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: payload normalize, metric selection, canonical instrument lookup, SQL upsert, integration verify, 운영 문서를 함께 고정해야 하기 때문이다.

## Architecture Or Approach

- 접근 방식:
  - companyfacts payload에서 selected `us-gaap` concepts만 읽는다.
  - 10-K/10-Q duration facts만 선택한다.
  - `entityName` 기준으로 canonical instrument exact-match lookup을 수행한다.
  - period row와 metric value row를 canonical market schema에 upsert한다.
- 핵심 tradeoff:
  - full concept coverage를 미루는 대신 deterministic metric subset만 먼저 연다.
- 피해야 할 함정:
  - instant balance sheet facts와 duration facts를 섞어 period semantics를 흐리는 것
  - alias/fuzzy match로 잘못된 instrument에 연결하는 것
  - filings metadata 없이 source document linkage를 필수로 가정하는 것

## Milestones

### Milestone 1

- 목표: companyfacts normalize와 SQL renderer를 구현한다.
- 산출물: `sec/models.py`, `sec/sql.py`, `sec/companyfacts.py`, `tests/test_sec_companyfacts.py`
- 검증: unit test로 companyfacts normalize, metric filtering, SQL rendering을 확인한다.

### Milestone 2

- 목표: runner와 CLI를 연결한다.
- 산출물: `cli.py`, `tests/test_ingest_cli.py`
- 검증: runner summary test와 CLI summary test가 통과한다.

### Milestone 3

- 목표: integration verify와 운영 문서를 마무리한다.
- 산출물: `tests/fixtures/sec_companyfacts_CIK0000320193.json`, `verify_sec_companyfacts_ingest.sh`, `docs/sec-companyfacts-ingest.md`, task docs
- 검증: docker 기반 companyfacts ingest verify와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `sec-filings-ingest` 완료
  - `event-instrument-impact-bootstrap` 완료
  - canonical `financial_statement_period`, `financial_metric_value` schema 존재
- 순서 제약:
  - canonical instrument row 없이 companyfacts upsert를 먼저 완료라고 보지 않는다
  - metric subset 확장은 baseline ingest 검증 후에만 한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 normalize code, SQL, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - companyfacts unit test 통과
  - CLI summary test 통과
  - docker 기반 companyfacts ingest verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-companyfacts-ingest` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: companyfacts ingest code, CLI, verify script, docs만 제거하면 기존 SEC pipeline 상태로 복귀한다.

## Open Questions

- 질문:
  - next step을 richer financial concept coverage와 retry policy 중 어디에 둘지
- 임시 가정:
  - 현재는 selected USD duration metrics만 먼저 고정한다.
