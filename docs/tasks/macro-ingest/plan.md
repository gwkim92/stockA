# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: macro-ingest
- 요청: FRED 기반 첫 실제 ingest 경로를 구현하고, 정규화 결과를 SQL upsert까지 연결한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: FRED 시리즈를 deterministic fixture 또는 live fetch로 읽어 `MacroSyncResult`로 정규화하고, CLI에서 요약과 SQL upsert 출력을 생성할 수 있다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 이 작업은 기존 ingest bootstrap 구조 위에 새 도메인 계층을 추가하고, 정규화 모델, CLI, 테스트, verification, task 문서가 함께 움직여야 해서 단계별 고정이 필요하다.

## Architecture Or Approach

- 접근 방식:
  - `ingest/sources/fred.py`의 request builder는 그대로 재사용한다.
  - `ingest/macro/`에 series spec, 정규화 로직, SQL renderer를 분리한다.
  - CLI는 summary 출력과 optional SQL file write까지만 담당한다.
  - 검증은 fixture 파일 기반으로 고정해 live API 의존성을 제거한다.
- 핵심 tradeoff:
  - direct DB execute를 미루는 대신 deterministic 검증성과 경계 명확성을 얻는다.
- 피해야 할 함정:
  - FRED raw payload 구조를 상위 계층까지 노출하는 것
  - 환경변수 없이는 테스트가 안 되는 구조
  - revision/vintage 문제를 지금 단계에서 과하게 일반화하는 것

## Milestones

### Milestone 1

- 목표: macro ingest 도메인 모델과 기본 series 세트를 정의한다.
- 산출물: `src/stockanalysis/ingest/macro/models.py`, `defaults.py`
- 검증: unit test에서 기본 series id를 확인하고 CLI `macro-default-series`가 동작한다.

### Milestone 2

- 목표: FRED payload 정규화와 SQL renderer를 구현한다.
- 산출물: `fred.py`, `sql.py`, fixture JSON
- 검증: fixture 기반 `load_macro_sync_result`와 SQL generation test가 통과한다.

### Milestone 3

- 목표: CLI, verification script, 문서를 마무리한다.
- 산출물: `cli.py` 확장, `docs/macro-ingest.md`, `scripts/verify_macro_ingest.sh`, task 문서
- 검증: `bash scripts/verify_macro_ingest.sh`, `awh verify --task macro-ingest`

## Dependencies

- 선행 조건:
  - `ingest-bootstrap` task 완료
  - `FRED` source adapter 존재
  - `macro.series`, `macro.observation` DDL 존재
- 순서 제약:
  - 기본 series spec 없이 CLI sync를 추가하지 않는다
  - 정규화 모델 없이 SQL renderer를 먼저 작성하지 않는다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 현재는 단일 agent가 macro 도메인 모델, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 병렬 이득이 작아 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: fixture 정규화가 끝난 뒤 한 번, verification script 통과 뒤 한 번
- 언제 handoff를 갱신할 것인가: `verify_macro_ingest.sh` 통과 후와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - 기본 series와 CLI listing이 동작한다
  - fixture 정규화와 SQL 생성이 테스트로 검증된다
  - verification script와 task readiness가 통과한다
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_ingest.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-ingest` 성공
  - placeholder 검색 결과가 비어 있다

## Rollback

- 어느 지점까지 되돌릴 수 있는가: `macro-sync` direct path에 문제가 생기면 `ingest-bootstrap` 상태로 되돌리고 `ingest/macro/`와 관련 CLI command만 제거하면 된다.

## Open Questions

- 질문:
  - SQL renderer가 장기적으로 canonical path인지, DB write runner의 중간 단계인지
- 임시 가정:
  - 현재 SQL renderer는 검증 가능한 중간 단계이며, 다음 task에서 DB execute runner를 붙인다.
