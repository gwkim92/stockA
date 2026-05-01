# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: macro-upsert-runner
- 요청: macro ingest 결과를 canonical Postgres에 실제 반영하는 runner를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `macro-upsert` CLI가 fixture 또는 live payload를 읽어 pipeline run을 생성하고 `macro.series`, `macro.observation` upsert를 실행한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 이 작업은 CLI, DB 실행기, SQL renderer, integration verify, task 문서가 함께 변해야 해서 단계별 고정이 필요하다.

## Architecture Or Approach

- 접근 방식:
  - DB 연결은 새 dependency를 추가하지 않고 `psql` 명령 래퍼로 처리한다.
  - `macro-sync`는 유지하고 새 `macro-upsert` runner를 추가한다.
  - `ops.pipeline_run`은 Python에서 별도 lifecycle로 관리한다.
- 핵심 tradeoff:
  - `psql` subprocess 경로는 간단하지만 장기적으로는 Python driver보다 기능이 제한된다.
- 피해야 할 함정:
  - SQL 생성기와 실행기 책임을 섞는 것
  - pipeline run 실패 상태를 남기지 못하는 것
  - 검증이 live API 또는 외부 DB에 묶이는 것

## Milestones

### Milestone 1

- 목표: `psql` 실행기와 runner 경계를 만든다.
- 산출물: `config.py`, `psql.py`, `macro/upsert.py`
- 검증: unit test로 성공/실패 상태 전이를 검증한다.

### Milestone 2

- 목표: CLI와 SQL renderer를 upsert 경로에 연결한다.
- 산출물: `cli.py`, `macro/sql.py`
- 검증: CLI summary test가 통과한다.

### Milestone 3

- 목표: integration 검증과 문서를 마무리한다.
- 산출물: `verify_macro_upsert_runner.sh`, `docs/macro-upsert-runner.md`, task docs
- 검증: fixture 기반 DB upsert와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `macro-ingest` 완료
  - migration/seed verify script 존재
  - docker 기반 Postgres 검증 경로 존재
- 순서 제약:
  - `psql` 실행기 없이 runner를 구현하지 않는다
  - pipeline run lifecycle 없이 observation source_run_id를 채우지 않는다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 runner 코드, 테스트, 검증, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위는 강하게 연결되어 있어 단일 흐름이 낫다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: runner unit test가 붙은 뒤 한 번, integration verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - pipeline run lifecycle test 통과
  - CLI summary test 통과
  - docker 기반 macro upsert 검증 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_upsert_runner.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-upsert-runner` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: `psql.py`, `macro/upsert.py`, CLI 추가 명령, verify script를 제거하면 이전 `macro-ingest` 상태로 돌아간다.

## Open Questions

- 질문:
  - 향후 `macro-upsert`를 multi-series batch로 확장할 때 run granularity를 series별로 둘지 batch별로 둘지
- 임시 가정:
  - 현재는 series별 run 한 건이 기본 단위다.
