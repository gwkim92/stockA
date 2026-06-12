# Task Contract

## Task

- 이름: scheduler-drift-hardening-v1
- 요청: EC2 운영 profile scheduler에서 기대 profile timer 누락이 재발하지 않도록 drift 감지와 검증을 강화한다.
- 담당: Codex
- 날짜: 2026-06-12

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `operating-data-profile-scheduler-status-report`가 기대 profile timer 전체의 누락/비활성 상태를 명시하고, 검증 스크립트가 `cross-asset-daily`를 포함한 8개 profile systemd manifest와 status report를 검사한다.

## Why

- EC2에서 FastAPI/Next.js는 정상이어도 `cross-asset-daily` systemd timer가 누락되면 cross-asset indicator/regime/linkage pipeline이 stale 상태가 된다.
- 수동 복구만으로는 다음 배포나 scheduler 재설치 때 같은 drift가 재발할 수 있다.

## Scope

- 포함:
  - profile scheduler status report에 missing/inactive drift metadata 추가
  - `cross-asset-daily` 포함 8개 profile 검증 강화
  - unit/verification script 갱신
  - task handoff 기록
- 제외:
  - 추천 scoring weight 변경
  - DB schema 변경
  - broker/order flow
  - production secret/env 파일 수정
  - AWS 보안그룹/인스턴스 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `tests/test_operating_data_profile_scheduler.py`
  - `scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `docs/tasks/scheduler-drift-hardening-v1/`
- 수정 금지 파일:
  - repo 밖 runtime env/secrets
  - `db/migrations/`
  - recommendation scoring/benchmark/evaluation split
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_operating_data_profile_scheduler`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task scheduler-drift-hardening-v1`

## Completion Criteria

- [x] status report가 `missing_timer_count`, `inactive_timer_count`, `drift_detected`, `missing_profiles`, `inactive_profiles`를 반환한다.
- [x] 누락된 expected timer가 있으면 `install_status=partial` 또는 `not_installed`로 드러난다.
- [x] 검증 스크립트가 8개 default profile과 `cross-asset-daily` systemd calendar를 확인한다.
- [x] 관련 테스트와 하네스 검증이 통과한다.
