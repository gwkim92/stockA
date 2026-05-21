# Task Contract

## Task

- 이름: ec2-systemd-profile-scheduler
- 요청: EC2 `stockanalysis-mvp-20260520`에서 운영 데이터 수집/분석을 profile별 `systemd` timer로 자동 실행한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: EC2에 `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly` timer가 설치/활성화되어 있고, `full-recovery`는 자동 timer에서 제외된다.

## Why

- 뉴스/AI는 짧은 주기로 stale 상태가 되지 않게 갱신되어야 한다.
- 주식 캔들은 무료 provider budget을 지키며 장 마감 후 일 1회 갱신되어야 한다.
- 추천/보유검토/페이퍼 검증은 최신 뉴스와 캔들 이후 일 1회 실행되어야 한다.
- 매크로와 성과 측정은 각각 주간/월간으로 충분하다.
- 모든 것을 한 job에 묶으면 실패 반경, API quota 사용, 재실행 비용이 커진다.

## Scope

- 포함:
  - repo의 profile scheduler invocation이 `operating-data-run --execute` 명령을 렌더하도록 보강
  - EC2에서 repo 최신화, focused 검증, systemd manifest 생성
  - systemd service/timer 설치, enable/start, timer 상태 확인
  - `/api/data-health`, 주요 API/Next route, systemd log 확인
- 제외:
  - HTTP/HTTPS security group 공개
  - 실거래 broker submission
  - DB schema/scoring/benchmark 변경
  - Mac LaunchAgents/`launchctl`
  - 유료 provider 도입

## Boundaries

- EC2 systemd timer는 `/opt/stockanalysis/runtime/data-operations.env` 같은 repo-outside env만 참조한다.
- systemd unit은 secret 값을 직접 포함하지 않는다.
- `full-recovery`는 수동 복구용으로만 유지한다.
- write는 `operating-data-run --execute` child command에서만 발생한다.
- market job은 기존 무료 provider budget ledger와 `--skip-if-fresh`/runner policy를 따른다.

## Verification Commands

- `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_operating_data_profile_scheduler tests.test_data_operations_cli -v`
- `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
- `systemd-analyze verify <generated service/timer files>`
- `sudo systemctl daemon-reload`
- `sudo systemctl enable --now <stockanalysis operating-data timers>`
- `systemctl list-timers --all | grep stockanalysis`
- authorized `GET /api/data-health`
- Next route smoke for `/data-health`, `/stocks`, `/intelligence`, `/paper-trading`, `/trading-readiness`, `/portfolio/coverage`, `/remediation`

## Done Criteria

- [x] EC2 services remain active.
- [x] EC2 stockanalysis timers are listed and scheduled.
- [x] timer-generated commands include `--execute`.
- [x] `/api/data-health` no longer reports scheduler as not installed.
- [x] no FastAPI/Next error logs are introduced.
- [x] task handoff records exact status and residual risks.
