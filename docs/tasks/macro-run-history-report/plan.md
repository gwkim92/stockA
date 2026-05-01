# Task Plan

이 문서는 guided single-agent보다 더 구조화된 실행이 필요한 작업에서 사용한다.

## Task

- 이름: macro-run-history-report
- 요청: 최근 macro upsert run 이력을 조회하는 report 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-18

## Goal

- 이 작업이 끝났을 때 달성되어야 하는 상태: `macro-run-history` CLI가 최근 run 이력, status 집계, per-run observation count를 JSON으로 반환한다.

## Why This Needs A Plan

- 왜 `contract.md`만으로 부족한가: 이 작업은 read-only query지만 SQL shape, CLI contract, integration verify, 운영 문서를 함께 고정해야 한다.

## Architecture Or Approach

- 접근 방식:
  - `psql` executor를 그대로 재사용한다.
  - Postgres에서 JSON report를 한 번에 구성하고 Python은 이를 parse해 그대로 반환한다.
  - `ops.pipeline_run` + `macro.observation.source_run_id`를 기준으로 recent run summary를 만든다.
- 핵심 tradeoff:
  - SQL 쪽 JSON 구성이 조금 복잡하지만 Python 후처리가 단순해진다.
- 피해야 할 함정:
  - run history query가 upsert runner와 중복 상태를 유지하도록 만드는 것
  - batch 적재가 남긴 series별 run을 무시하는 것

## Milestones

### Milestone 1

- 목표: report query와 CLI를 구현한다.
- 산출물: `macro/report.py`, `cli.py`
- 검증: unit test로 payload parsing과 status filter를 확인한다.

### Milestone 2

- 목표: batch upsert 후 report integration verify를 추가한다.
- 산출물: `verify_macro_run_history_report.sh`
- 검증: 2-series batch 후 run_count/status_counts를 확인한다.

### Milestone 3

- 목표: 운영 문서와 task artifact를 마무리한다.
- 산출물: `docs/macro-run-history-report.md`, task docs
- 검증: readiness 검증과 placeholder 검증 통과

## Dependencies

- 선행 조건:
  - `macro-upsert-runner` 완료
  - `macro-batch-upsert` 완료
  - docker 기반 verify 경로 존재
- 순서 제약:
  - report shape를 고정하기 전 integration verify를 쓰지 않는다
  - recent run query가 먼저 구현되기 전 문서 예시를 고정하지 않는다

## Ownership

- 한 번에 누가 무엇을 책임지는가: 단일 agent가 SQL query, CLI, 테스트, 문서를 모두 책임진다.
- 병렬 가능한가: 현재 범위에서는 단일 흐름이 적합하다.

## Checkpoints

- 언제 상태를 다시 평가할 것인가: unit test가 붙은 뒤 한 번, integration verify가 통과한 뒤 한 번
- 언제 handoff를 갱신할 것인가: integration verify와 readiness 검증 후

## Verification Gates

- milestone별 통과 조건:
  - report unit test 통과
  - CLI summary test 통과
  - docker 기반 batch+report integration verify 통과
- 최종 통과 조건:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_macro_run_history_report.sh` 성공
  - `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task macro-run-history-report` 성공

## Rollback

- 어느 지점까지 되돌릴 수 있는가: report query, CLI 명령, verify script, docs만 제거하면 `macro-batch-upsert` 상태로 복귀한다.

## Open Questions

- 질문:
  - report default limit를 20으로 유지할지 더 작게 조정할지
- 임시 가정:
  - 현재는 recent troubleshooting 용도로 20을 유지한다.
