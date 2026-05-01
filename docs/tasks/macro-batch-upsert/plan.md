# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: macro-batch-upsert
- 요청: 여러 기본 거시 series를 한 번에 적재하는 batch runner를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `macro-batch-upsert` CLI가 default macro series 목록 또는 사용자가 고른 일부 목록을 순차 실행해 canonical DB에 적재한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: batch runner는 fixture 전략, 요약 포맷, 실패 처리, integration verify까지 함께 고정해야 해서 구조를 먼저 잠가야 한다.

## Architecture Or Approach

- 접근 방식:
  - 기존 `run_macro_upsert`를 재사용한다.
  - batch runner는 spec resolution, fixture path resolution, per-series summary aggregation만 담당한다.
  - batch는 순차 실행으로 유지하고, 각 series는 독립 `pipeline_run`을 만든다.
- 핵심 tradeoff:
  - 단순 순차 실행은 느리지만, 실패 격리와 검증 단순성이 좋다.
- 피해야 할 함정:
  - batch run 하나로 여러 series를 한 transaction에 묶는 것
  - fixture 파일 명명 규칙 없이 ad-hoc path를 받는 것

## Milestones

### Milestone 1

- 목표: spec resolver와 batch runner를 구현한다.
- 산출물: `macro/upsert.py`
- 검증: unit test로 batch summary와 failure continuation을 확인한다.

### Milestone 2

- 목표: CLI와 fixture 전략을 연결한다.
- 산출물: `cli.py`, FEDFUNDS fixture
- 검증: CLI summary test와 fixture directory success test가 통과한다.

### Milestone 3

- 목표: integration verify와 문서를 마무리한다.
- 산출물: `verify_macro_batch_upsert.sh`, `docs/macro-batch-upsert.md`, task docs
- 검증: docker 기반 2-series upsert와 readiness 검증이 통과한다.

## Dependencies

- 선행 조건:
  - `macro-upsert-runner` 완료
  - `psql` command runner 존재
  - docker 기반 verify 경로 존재
- 순서 제약:
  - fixture directory naming을 정하기 전 integration verify를 쓰지 않는다
  - batch summary shape를 정하기 전 CLI 출력 형식을 고정하지 않는다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 runner, fixture, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위는 강하게 연결되어 있어 단일 흐름이 낫다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, docker verify 통과 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - batch unit test 통과
  - CLI summary test 통과
  - 2-series integration verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_batch_upsert.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-batch-upsert` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: batch 관련 CLI와 fixture logic, verify script, docs만 제거하면 `macro-upsert-runner` 상태로 복귀한다.

## Open Questions

- 질문:
  - batch 실행 순서를 default series 정의 순서에 고정할지
- 임시 가정:
  - 현재는 요청한 series 순서, 없으면 default 정의 순서를 사용한다.
