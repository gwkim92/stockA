# Review

## Summary

- EC2 `systemd` 기반 profile scheduler activation을 완료했다.
- 자동 실행 대상은 `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly` 다섯 개다.
- `full-recovery`는 수동 실행으로 유지했다.

## Findings

- `market-daily`와 `decision-daily`가 둘 다 cadence default 때문에 같은 시각에 잡히는 문제가 있었고, profile별 default schedule을 추가해 `decision-daily`를 19:00 NY로 분리했다.
- `/api/data-health`는 실제 systemd 상태를 몰라 `scheduler.install_status=not_installed`를 계속 반환할 수 있었고, repo-outside status report를 읽어 `installed`로 표시하도록 수정했다.

## Verification

- Local focused unit tests passed.
- EC2 focused unit tests and scheduler invocation verifier passed.
- `systemd-analyze verify` passed for generated service/timer files.
- EC2 systemd timers are active and scheduled.
- EC2 `/api/data-health` returns `overall_status=healthy` and `profile_scheduler.active_timer_count=5`.
- EC2 route smoke returned HTTP `200` for core cockpit routes.

## Residual Risks

- `market-universe-weekly`와 `sec-filings-weekly`는 아직 별도 profile timer에 포함되지 않았다.
- scheduler status report는 현재 snapshot 파일이며, timer 상태 변화까지 자동 갱신하는 별도 reporter는 없다.
- 공개 HTTPS 배포는 아직 하지 않았다.
