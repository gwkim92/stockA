# Task Contract

## Task

- 이름: operating-data-profile-scheduler
- 요청: 전체 운영 데이터를 매번 하나로 묶어 실행하지 않고, 뉴스/AI, 주식 캔들, 추천/보유검토, 매크로, 성과를 각기 다른 주기로 자동화할 수 있게 backend runner profile을 분리한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations operating-data-run --profile <profile>`이 profile별 step subset을 preview/execute하고, `full-recovery`는 배포/장애복구용 전체 실행으로 유지된다.

## Why

- 뉴스 수집/분석은 짧은 주기로 돌아야 한다.
- 주식 캔들 보강은 무료 provider budget과 시장 데이터 준비 시각을 고려해 장 마감 후 일 1회가 합리적이다.
- 추천/신호/보유검토는 최신 캔들/뉴스 이후 일 1회가 적합하다.
- 매크로와 성과 측정은 각각 주간/월간 주기가 적합하다.
- 전체 runner를 그대로 scheduler에 걸면 비용, API quota, 실패 반경이 커진다.

## Scope

- 포함:
  - `operating-data-run --profile` CLI option
  - `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly`, `full-recovery` profile
  - 뉴스/AI intraday cadence registry visibility
  - profile별 source position dependency 분리
  - focused tests and verification script updates
- `operating-data-profile-scheduler-invocation-plan` CLI boundary for target-based invocation packet emission
- `systemd` 대상일 때 시스템 cron식 변환 제약을 사전 검증해 `*/30` 또는 시간대 범위와 같은 미지원 패턴을 즉시 reject
- 제외:
  - EC2 systemd timer 실제 설치
  - DB schema 변경
  - scoring formula 변경
  - broker submission 또는 kill switch 해제
  - 유료 data provider 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/manual_local_ingest_smoke.py`
  - `src/stockanalysis/operations/scheduler_install.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `scripts/verify_operating_data_orchestrator.sh`
  - task docs, roadmap docs, verification docs
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - benchmark/evaluation split
  - scoring formula
  - broker credential files
  - host scheduler install state

## Boundaries

- 기본 실행은 계속 no-write preview다.
- write는 명시적 `--execute`에서만 가능하다.
- `full-recovery`는 자동 주기 실행 대상이 아니라 배포 smoke/장애 복구용이다.
- profile report는 DB URL, API key, bearer token을 노출하지 않는다.
- Mac LaunchAgents/`launchctl`은 계속 이 작업 범위 밖이다.

## Verification Commands

- 검증에 사용할 명령:
- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cli tests.test_data_operations_cadence`
- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_profile_scheduler`
- `bash scripts/verify_operating_data_orchestrator.sh`
- `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
- `test_systemd_target_rejects_unsupported_schedule_pattern` in `tests.test_operating_data_profile_scheduler`
- `PYTHONPATH=src python3 -m compileall src tests`
- `git diff --check`

## Done Criteria

- [x] `news-intraday`가 뉴스/AI step만 계획한다.
- [x] `market-daily`가 candle refresh step만 계획한다.
- [x] `decision-daily`가 추천/신호/보유검토 step만 계획하고 뉴스/매크로를 섞지 않는다.
- [x] `full-recovery`가 전체 step을 dependency order로 유지한다.
- [x] 뉴스/AI cadence가 data-health registry에서 intraday로 노출된다.
