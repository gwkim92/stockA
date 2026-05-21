# Task Contract

## Task

- 이름: ec2-weekly-reference-scheduler-status
- 요청: EC2 자동 운영에서 빠진 `market-universe-weekly`, `sec-filings-weekly`를 profile scheduler에 편입하고, `/api/data-health`가 보는 scheduler status report를 수동 snapshot이 아니라 backend CLI로 갱신 가능하게 만든다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: EC2에 주간 market universe/SEC filings timer가 추가되고, `stockanalysis-operations operating-data-profile-scheduler-status-report`가 systemd timer 상태를 repo-outside JSON으로 생성한다.

## Why

- `/api/data-health` cadence registry에는 `market-universe-weekly`, `sec-filings-weekly`가 존재한다.
- 이전 EC2 timer set은 뉴스/AI, 캔들, 의사결정, 매크로, 성과만 포함해 두 주간 기준 데이터 수집이 자동 실행 범위 밖이었다.
- scheduler status JSON이 설치 시점 snapshot이면 timer 상태 변화가 화면에 늦게 반영된다.

## Scope

- 포함:
  - `operating-data-run` profile에 `market-universe-weekly`, `sec-filings-weekly` 추가
  - profile별 systemd schedule에 universe `07:00 Monday`, SEC `08:00 Monday` 추가
  - scheduler status report 생성 CLI 추가
  - EC2 manifest 재생성, timer 설치/활성화, status report 갱신
  - focused tests and verification updates
- 제외:
  - DB schema 변경
  - scoring/benchmark 변경
  - 유료 provider 도입
  - HTTP/HTTPS 공개
  - 실거래 broker submission

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_operating_data_profile_scheduler.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - `scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `docs/tasks/ec2-weekly-reference-scheduler-status/*`
- 수정 금지 파일:
  - `db/migrations/`
  - `apps/web/`
  - repo-inside env/secret files
  - benchmark/evaluation/scoring files
  - broker/order submission implementation

## Boundaries

- generated systemd unit은 repo-outside env 파일만 참조한다.
- SEC filings 첫 slice는 기존 검증된 기본 CIK `320193`와 `max-filings=3`을 사용한다.
- `full-recovery`는 자동 timer에서 제외하지만 전체 복구 시 새 reference weekly steps를 포함한다.
- status report는 secret 값과 repo-inside env path를 노출하지 않는다.

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_operating_data_orchestrator tests.test_operating_data_profile_scheduler tests.test_data_operations_cli tests.test_frontend_live_adapter -v`
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
  - `git diff --check`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ec2-weekly-reference-scheduler-status`
  - EC2 `systemd-analyze verify /opt/stockanalysis/runtime/operating-data-profile-scheduler-manifests/*.service /opt/stockanalysis/runtime/operating-data-profile-scheduler-manifests/*.timer`
  - EC2 `systemctl list-timers --all | grep stockanalysis-operating-data`
  - authorized EC2 `GET /api/data-health`

## Done Criteria

- [ ] `market-universe-weekly` profile exists and renders a systemd timer.
- [ ] `sec-filings-weekly` profile exists and renders a systemd timer.
- [ ] EC2 timer count increases from 5 to 7.
- [ ] scheduler status report CLI writes installed/active timer state.
- [ ] `/api/data-health` reports active profile scheduler count from the generated status report.
- [ ] task handoff records verification and remaining risks.
