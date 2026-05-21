# Session Handoff

## Active Task

- 이름: ec2-weekly-reference-scheduler-status
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - task contract created.
  - `market-universe-weekly` and `sec-filings-weekly` operating data profiles added.
  - full recovery plan now includes market universe and SEC filing reference refresh before news, market, decision, macro, and performance steps.
  - profile scheduler default systemd schedules now include Monday 07:00 universe and Monday 08:00 SEC refresh.
  - backend CLI `operating-data-profile-scheduler-status-report` added to read systemd timer state into a secret-free repo-outside JSON report.
  - local focused unit, scheduler invocation, compile, diff, and roadmap checks passed.
- 진행 중:
  - EC2 deployment of the new 7-profile scheduler manifest and recurring scheduler-status refresh timer.
- 막힌 점:
  - none.

## Exact Next Step

- exact next step: commit/push the local scheduler changes, pull them on EC2, regenerate systemd manifests, enable the 2 new weekly timers, install the scheduler status refresh timer, and verify `/api/data-health` reports 7 active profile timers.

## Verification

- Passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_operating_data_orchestrator tests.test_operating_data_profile_scheduler tests.test_data_operations_cli tests.test_frontend_live_adapter -v`
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
  - `git diff --check`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
- Not yet passed:
  - EC2 `systemd-analyze verify` for regenerated 7-profile manifests.
  - EC2 `systemctl list-timers --all | grep stockanalysis-operating-data`.
  - authorized EC2 `GET /api/data-health` after timer install.
  - AWH verify until this handoff is present and rerun.

## Risks

- SEC filing refresh defaults to Apple CIK `320193` with `max-filings=3`; broader SEC coverage requires a later configurable issuer list.
- Market universe and SEC filing jobs are weekly metadata/reference jobs. They do not replace intraday news analysis or daily candle refresh.
- This task does not expose public HTTP/HTTPS and does not enable broker order submission.
