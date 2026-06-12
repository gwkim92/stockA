# Session Handoff

## Active Task

- 이름: scheduler-drift-hardening-v1
- 담당: Codex
- 날짜: 2026-06-12

## Current Status

- 완료:
  - profile scheduler status report에 missing/inactive drift metadata를 추가했다.
  - `cross-asset-daily` 누락 timer를 drift로 잡는 unit test를 추가했다.
  - scheduler verification script가 8개 default profile과 `cross-asset-daily` calendar를 확인하도록 갱신했다.
  - EC2의 시스템 `python3.9`와 venv `python3.12` 차이를 피하기 위해 verify script에 `PYTHON_BIN` override를 추가했다.
- 막힌 점:
  - 아직 없음.

## Context

- EC2에서 `cross-asset-daily` timer 누락으로 cross-asset stale pipeline gate가 열렸고, 수동 profile 실행 및 timer 설치로 운영 상태는 복구됐다.
- 이 task는 같은 누락이 배포/검증 단계에서 재발하지 않도록 repo 검증을 강화한다.

## Files Touched

- 생성:
  - `docs/tasks/scheduler-drift-hardening-v1/contract.md`
  - `docs/tasks/scheduler-drift-hardening-v1/handoff.md`
- 수정:
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `tests/test_operating_data_profile_scheduler.py`
  - `scripts/verify_operating_data_profile_scheduler_invocation.sh`

## Decisions

- status report는 expected profile 목록을 기준으로 timer를 검사한다.
- `systemctl show <timer> -p LoadState`가 `not-found`이거나 active/load state가 비어 있으면 missing drift로 분류한다.
- inactive timer와 missing timer를 분리해 화면/API가 원인을 다르게 설명할 수 있게 했다.
- EC2 ad-hoc verification은 `PYTHON_BIN=/opt/stockanalysis/venv/bin/python bash scripts/verify_operating_data_profile_scheduler_invocation.sh`처럼 실행한다.
- 추천 weight, broker/order boundary, production env/secrets는 변경하지 않았다.

## Verification

- 통과:
  - `PYTHONPATH=src python3 -m unittest tests.test_operating_data_profile_scheduler`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task scheduler-drift-hardening-v1`

## Exact Next Step

- exact next step: commit the scheduler drift hardening changes, push `develop`, and pull the updated code on EC2.
