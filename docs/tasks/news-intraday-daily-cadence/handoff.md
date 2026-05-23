# Session Handoff

## Active Task

- 이름: news-intraday-daily-cadence
- 담당: Codex
- 날짜: 2026-05-23

## Current Status

- 완료:
  - `news-intraday` default schedule을 월-금 장중 30분 간격에서 매일 2시간 간격으로 변경했다.
  - scheduler unit test와 verification script 기대값을 새 systemd calendar에 맞췄다.
  - GitHub branch `codex/local-mvp-runtime-aws-bootstrap`에 commit `6759c16`을 push했다.
  - EC2 `/opt/stockanalysis/app`를 `6759c16`으로 fast-forward 배포했다.
  - EC2에서 profile scheduler manifests를 재생성했고 `systemd-analyze verify`를 통과했다.
  - EC2 `/etc/systemd/system`에 regenerated service/timer files를 설치하고 `systemctl daemon-reload` 후 7개 profile timer를 enable/start했다.
  - 설치 직후 `Persistent=true`가 놓친 뉴스 실행분을 한 번 트리거했고 `stockanalysis-operating-data-news-intraday.service`는 `status=0/SUCCESS`로 끝났다.
  - 해당 즉시 실행은 RSS 5건을 추가했고 번역도 완료되어 RSS source document 상태가 `translated=241`, `pending=0`, `total=241`이 됐다.
  - `stockanalysis-operating-data-news-intraday.timer`는 `SubState=waiting`, 다음 실행 `Sat 2026-05-23 10:00:00 UTC`로 확인됐다.
  - scheduler status report는 `status=installed`, `active_timer_count=7`, `timer_count=7`로 갱신됐다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Implemented

- `DEFAULT_PROFILE_SCHEDULES["news-intraday"] = "0 0,2,4,6,8,10,12,14,16,18,20,22 * * *"`
- systemd 변환 결과:
  - `OnCalendar=*-*-* 00,02,04,06,08,10,12,14,16,18,20,22:00 America/New_York`

## Verification

- Passed:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_operating_data_profile_scheduler tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_command_writes_output_and_markdown tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_output tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_manifest_output_root`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task news-intraday-daily-cadence`
  - EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_operating_data_profile_scheduler ...`
  - EC2 `PATH=/opt/stockanalysis/venv/bin:$PATH bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - EC2 `systemd-analyze verify /opt/stockanalysis/runtime/operating-data-profile-scheduler-manifests/*.service /opt/stockanalysis/runtime/operating-data-profile-scheduler-manifests/*.timer`
  - EC2 `systemctl list-timers --all stockanalysis-operating-data-news-intraday.timer --no-pager`

## Exact Next Step

- exact next step: observe the next scheduled `news-intraday` run at `2026-05-23 10:00:00 UTC` and confirm `/data-health` still reports scheduler status installed plus translation pending count stays at 0 after any newly collected RSS items.
