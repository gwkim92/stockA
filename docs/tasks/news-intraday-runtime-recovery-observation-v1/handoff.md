# news-intraday-runtime-recovery-observation-v1 Handoff

## Current Status

- 완료: observation evidence collected and documented.
- 시작: 2026-06-03
- 완료: 2026-06-03

## Findings

- EC2 app commit at observation time: `7d0f382`.
- `stockanalysis-web.service` and `stockanalysis-frontend-api.service` are active.
- `stockanalysis-operating-data-news-intraday.timer` is active.
- During the run, the timer showed `Trigger: n/a` because the oneshot service was still running. After completion the next trigger was scheduled normally.

## Latest Scheduled Run Evidence

- service: `stockanalysis-operating-data-news-intraday.service`
- scheduled start: `2026-06-03T10:00:10Z`
- systemd result: `status=0/SUCCESS`
- service completed at: `2026-06-03T10:02:06Z`
- next timer: `2026-06-03T12:00:00Z`
- profile report: `/opt/stockanalysis/runtime/operating-data-profile-scheduler-reports/news-intraday-operating-data-run.json`
- profile result: `run_status=completed`, `failed_step_count=0`

## Step Evidence

- `news-korean-translation`: `status=succeeded`, `report_status=completed`, `run_id=3073`, `updated_document_count=10`, `failed_document_count=0`
- `news-ai-evidence`: `status=succeeded`, `report_status=completed`, `failed_candidate_count=0`
- `cycle-ai-duplicate-title-cleanup`: `status=succeeded`, `run_id=3075`, `candidate_count=0`
- `news-ai-eval`: `status=succeeded`, `run_id=3076`, `eval_run_id=157`
- `macro-event-propagation`: `status=succeeded`, `run_id=3077`, `candidate_count=199`
- `hierarchical-impact-propagation`: `status=succeeded`, `run_id=3078`, `candidate_count=1040`

## Data Health Evidence

- `/api/data-health.overall_status=healthy`
- `/api/data-health.open_gates=[]`
- `news-korean-translation-intraday.latest_status=succeeded`
- `news-korean-translation-intraday.latest_run_id=pipeline-run-3073`
- `news_ai_eval_quality.status=passed`
- `news_ai_eval_quality.eval_run_id=eval-run-157`
- `news_ai_eval_quality.failed_case_count=0`

## AI Invocation Evidence

- Latest 10 `news-rss-korean-translation` model invocations after the scheduled run were all `succeeded`.
- Latest translation invocation observed: `invocation_id=4233`, `created_at=2026-06-03T10:01:58.630538Z`, `status=succeeded`.
- `live_ai_invocation_health.status=recovered_with_recent_failures` remains because the 48-hour rolling window still includes prior failures.
- Latest failure timestamp remains `2026-06-03T00:00:52.821749Z`; no new `crowded` failure was observed after the fix.

## Next Step

- exact next step: stop this recovery observation unless the next scheduled runs produce new failures. Continue with broader project work: outcome maturity wait remains managed until `2026-06-24`, and recommendation weight review remains blocked until mature outcome evidence exists.
