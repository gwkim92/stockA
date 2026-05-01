# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: ingest-bootstrap
- 요청: collector 계층의 첫 코드 골격과 검증 경로를 추가한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: source adapter, registry, CLI, 테스트, 문서가 존재하고, 후속 ingest 구현이 이 구조 위에서 진행될 수 있다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 이번 작업은 코드 구조, 소스 선택, seed alignment, 검증 경로를 동시에 조정하므로 단순 파일 추가보다 상호의존성이 크다.

## Architecture Or Approach

- 접근 방식:
  - stdlib 기반 Python package로 시작한다.
  - source adapter는 요청 생성과 설명 책임까지만 가진다.
  - 실제 DB upsert는 다음 단계로 미룬다.
- 핵심 tradeoff:
  - 빠르게 동작하는 bootstrap 골격을 우선하고, persistence/retry는 뒤로 미룬다.
- 피해야 할 함정:
  - 곧바로 DB write까지 넣어 ingest 구조를 과도하게 키우는 것
  - source selection 근거 없이 임의 provider를 늘리는 것

## Milestones

### Milestone 1

- 목표: 프로젝트와 source scope를 고정한다.
- 산출물: `pyproject.toml`, `docs/ingest-bootstrap.md`, seed alignment update
- 검증: README와 문서에서 ingest bootstrap 범위가 명확해야 한다.

### Milestone 2

- 목표: source adapter와 CLI를 구현한다.
- 산출물: `src/stockanalysis/ingest/`
- 검증: `list-sources`, `describe-source`, `build-request`가 동작해야 한다.

### Milestone 3

- 목표: 테스트와 verification 경로를 추가한다.
- 산출물: `tests/`, `scripts/verify_ingest_bootstrap.sh`
- 검증: compile, unittest, CLI smoke가 성공해야 한다.

## Dependencies

- 선행 조건:
  - `seed-bootstrap` task 완료
  - priority 1 schema와 seed 구조 존재
- 순서 제약:
  - source selection 문서화 없이 source code를 늘리지 않는다
  - CLI와 tests는 adapter 구조가 먼저 정리된 뒤 추가한다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 문서, package bootstrap, source adapter, tests를 모두 책임진다.
- 병렬 가능한가: 현재 범위는 단일 흐름이 더 단순하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가:
  - source adapter 구현 후
  - 테스트/검증 실행 후
- 언제 handoff를 갱신할 것인가:
  - 검증 결과 확보 직후

## Verification Gates

- milestone별 통과 조건:
  - 문서가 ingest bootstrap 필요성과 source 선택을 설명한다
  - adapter와 CLI가 존재한다
  - tests와 verification script가 존재한다
- 최종 통과 조건:
  - `bash scripts/verify_ingest_bootstrap.sh` 성공
  - `awh verify --task ingest-bootstrap` 성공
  - placeholder 없음

## Rollback

- 어느 지점까지 되돌릴 수 있는가: live fetch entrypoint가 불안정하면 adapter/registry/CLI의 dry-run 기능만 남기는 단계까지 후퇴 가능하다.

## Open Questions

- 질문:
  - DB insert 계층을 언제 collector와 연결할지
- 임시 가정:
  - 다음 단계에서 source별 raw fetch/store/upsert task로 분리한다.
