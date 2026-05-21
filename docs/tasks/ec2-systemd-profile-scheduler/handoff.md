# Session Handoff

## Active Task

- 이름: ec2-systemd-profile-scheduler
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - EC2 `stockanalysis-mvp-20260520`에 profile별 `systemd` timer를 설치/활성화했다.
  - 설치된 timer:
    - `stockanalysis-operating-data-news-intraday.timer`: `Mon..Fri *-*-* 09..18:00/30 America/New_York`
    - `stockanalysis-operating-data-market-daily.timer`: `Mon..Fri *-*-* 18:35 America/New_York`
    - `stockanalysis-operating-data-decision-daily.timer`: `Mon..Fri *-*-* 19:00 America/New_York`
    - `stockanalysis-operating-data-macro-weekly.timer`: `Mon *-*-* 07:30 America/New_York`
    - `stockanalysis-operating-data-performance-monthly.timer`: `*-*-01 09:30 America/New_York`
  - `full-recovery`는 timer로 설치하지 않고 수동 복구/배포 smoke 용도로 남겼다.
  - 모든 generated service의 `ExecStart`는 `stockanalysis.operations.cli operating-data-run --profile <profile> --execute`를 호출한다.
  - `stockanalysis-operating-data-news-intraday.service`를 수동 start해 systemd 경로 실행을 검증했고 status `SUCCESS`로 종료했다.
  - `/api/data-health`는 `overall_status=healthy`, `scheduler.install_status=installed`, `scheduler.activation.status=installed`, `profile_scheduler.active_timer_count=5`를 반환한다.
  - 주요 Next route smoke: `/`, `/data-health`, `/stocks`, `/intelligence`, `/paper-trading`, `/trading-readiness`, `/portfolio/coverage`, `/remediation`, `/recommendations/recommendation-1`, `/theses/thesis-1` 모두 HTTP `200`.
  - FastAPI/Next/systemd news service 최근 로그에서 `Traceback`, `FrontendApiError`, `digest`, HTTP 500, non-zero service exit을 발견하지 못했다.

## Verification

- Local:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_operating_data_profile_scheduler -v`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_uses_profile_scheduler_status_report -v`
- EC2:
  - `PATH=/opt/stockanalysis/venv/bin:$PATH bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `systemd-analyze verify /opt/stockanalysis/runtime/operating-data-profile-scheduler-manifests/*.service /opt/stockanalysis/runtime/operating-data-profile-scheduler-manifests/*.timer`
  - `sudo systemctl enable --now stockanalysis-operating-data-*.timer`
  - `sudo systemctl start stockanalysis-operating-data-news-intraday.service`
  - authorized `GET /api/data-health`
  - Next route smoke listed above

## Exact Next Step

- 다음 세션은 이것부터 시작:
  - `market-universe-weekly`와 `sec-filings-weekly`도 profile scheduler 안으로 편입할지 결정한다. 현재 둘은 기존 data-health cadence에는 남아 있지만 이번 EC2 profile timer scope에는 포함하지 않았다.
  - timer status report를 일회성 파일이 아니라 주기적으로 갱신할지 결정한다. 현재 `/opt/stockanalysis/runtime/operating-data-profile-scheduler-status.json`은 설치 직후 생성된 snapshot이다.

## Risks

- HTTP/HTTPS는 아직 보안그룹에서 열지 않았고, 사용자는 SSH tunnel로 접속한다.
- `Twelve Data` 무료 budget은 timer 실행 시 기존 ledger와 runner guardrail에 의존한다.
- `market-universe-weekly`와 `sec-filings-weekly`는 이번 timer set에 포함되지 않아 장기적으로 별도 자동화 편입이 필요하다.
- 실거래 broker submission은 여전히 비활성이고, trading readiness는 kill switch/paper validation에 의해 block될 수 있다.
