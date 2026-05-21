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
  - EC2 pulled commit `fdff62f`, regenerated 7-profile systemd manifests, and enabled all 7 operating data profile timers.
  - EC2 installed `stockanalysis-operating-data-scheduler-status.timer` to refresh scheduler status JSON every 15 minutes.
  - Manual EC2 starts for `market-universe-weekly` and `sec-filings-weekly` completed with `run_status=completed` and 0 failed steps.
  - `/api/data-health` reports `overall_status=healthy`, scheduler activation `installed`, and 7/7 active profile timers.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Exact Next Step

- exact next step: observe the next scheduled `news-intraday`, `market-daily`, and Monday weekly timer runs in `/data-health`; then split child-job log freshness into a separate task if a timer is active but provider execution fails.

## Verification

- Passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_operating_data_orchestrator tests.test_operating_data_profile_scheduler tests.test_data_operations_cli tests.test_frontend_live_adapter -v`
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
  - `git diff --check`
  - `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ec2-weekly-reference-scheduler-status`
  - EC2 `PATH=/opt/stockanalysis/venv/bin:$PATH bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
  - EC2 `systemd-analyze verify` for regenerated 7-profile manifests.
  - EC2 `systemctl list-timers --all stockanalysis-operating-data-*.timer --no-pager`: 7 operating profile timers plus 1 scheduler-status helper timer active.
  - EC2 authorized `/api/data-health`: `overall_status=healthy`, `profile_active_timer_count=7`, `profile_timer_count=7`.
  - EC2 manual starts:
    - `stockanalysis-operating-data-market-universe-weekly.service`: succeeded, 0 failed steps.
    - `stockanalysis-operating-data-sec-filings-weekly.service`: succeeded, 0 failed steps.
  - EC2 core route smoke returned 200 for `/`, `/data-health`, `/stocks`, `/intelligence`, `/paper-trading`, `/trading-readiness`, `/portfolio/coverage`, `/recommendations/recommendation-1`, `/theses/thesis-1`.
  - EC2 recent frontend/API/weekly service logs have no real traceback, exception, failed, critical, or fatal entries.
- Not passed:
  - none for this slice.

## Risks

- SEC filing refresh defaults to Apple CIK `320193` with `max-filings=3`; broader SEC coverage requires a later configurable issuer list.
- Market universe and SEC filing jobs are weekly metadata/reference jobs. They do not replace intraday news analysis or daily candle refresh.
- Scheduler status reads systemd state only. Provider-level failures still require pipeline run history and artifact log inspection.
- This task does not expose public HTTP/HTTPS and does not enable broker order submission.
