# operations-ai-cyclemap-quality-v1 Handoff

## Status

- status: implemented_local_verified_ec2_smoked_pending_deploy.
- started_at: 2026-07-01.
- in progress: deployment and final EC2 post-deploy smoke remain.
- current status: implemented locally, verified with local type/test/build/e2e after final component extraction and copy cleanup, and EC2 runtime recovery commands were smoke-tested. Pending git commit, `develop` merge, and EC2 deploy.

## Current Status

- current status: implemented locally and EC2 recovery-smoked; deployment to `develop` is still pending.

## Next Step

- exact next step: commit the feature branch, merge/push `develop`, pull `develop` on EC2, restart FastAPI/Next services, and repeat EC2 route/data-health smoke.

## Evidence Log

- Branch: `feature/operations-ai-cyclemap-quality-v1`.
- Initial local E2E baseline: `66/69` passed; `/cycle-map` failed investor internal-copy gate because visible text contained `breadth_score`.
- EC2 alert recovery:
  - First attempt with `/opt/stockanalysis/runtime/data-operations.env` failed because the alert destination is configured in `/opt/stockanalysis/runtime/frontend-api.env`, not data operations env.
  - Retried `alert-destination-test-run --env-file /opt/stockanalysis/runtime/frontend-api.env --execute`.
  - `/api/data-health.alert_destination.status=external_destination_verified`, `attention_required=false`, `last_test_status=passed`, `test_recent=true`.
- EC2 outcome and portfolio recovery:
  - `recommendation-outcome-due-action-router-run --as-of-date 2026-07-01 --execute` completed with parent `run_id=8747`, `eval_run_id=594`, child `run_id=8748`, `eval_run_id=593`, `action_status=outcome_calibration_executed`.
  - `portfolio-review-feedback-action-router-run --as-of-date 2026-07-01 --execute` completed with parent `run_id=8759`, `eval_run_id=596`, child `run_id=8760`, `eval_run_id=595`, `action_status=feedback_executed`.
  - Both reported `automatic_weight_change_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- EC2 live AI recovery:
  - `cycle-community-ai-summary-v2-run --provider codex_oauth --execute` completed with `run_id=8746`, `inserted_summary_count=17`, `failed_summary_count=0`, invocation ids `12549` through `12565`.
  - `news-rss-translation-run --provider codex_oauth --limit 1 --execute` completed with `run_id=8761`, `invocation_id=12566`, `failed_document_count=0`.
  - `news-rss-ai-extract-run --provider codex_oauth --limit 1 --execute` completed with `run_id=8762`, `invocation_id=12567`, `failed_candidate_count=0`; the one candidate was validator-rejected as `rejected_no_validated_impacts`, which is a quality block, not an invocation failure.
  - `/api/data-health.live_ai_invocation_health.status=recovered_with_recent_failures`, `attention_required=false`, `critical_latest_unhealthy_count=0`.
- Remaining EC2 open gates after recovery:
  - `benchmark_drift_quality_attention`
  - `portfolio_review_decision_history_attention`
  - `portfolio_review_feedback_calibration_attention`
  - `portfolio_review_feedback_cadence_attention`
  - `recommendation_outcome_calibration_attention`
  - `recommendation_outcome_maturity_attention`
  - These are outcome/feedback/benchmark managed review gates, not auth/alert/AI invocation blockers.
- Frontend refactor:
  - `/cycle-map` route shrank from 436 lines to 224 lines by moving presentation logic to `apps/web/src/app/cycle-map/_components/cycleMapModel.ts` and `apps/web/src/app/cycle-map/_components/CycleImpactPathSection.tsx`.
  - `apps/web/src/lib/frontend-api.ts` normalizers were split into `frontend-normalizers-market.ts`, `frontend-normalizers-operations.ts`, `frontend-normalizers-paper.ts`, `frontend-normalizers-ai-evidence.ts`, `frontend-normalizers-performance.ts`, and `frontend-normalizer-utils.ts`.
  - Public frontend fetch functions remain in `frontend-api.ts`.
  - `/cycle-map` copy mapping now removes raw cycle labels such as `subtheme`, `cooling`, `TECHNOLOGY`, `community`, `형성 중`, and `확인 국면` from investor-facing text.
- Local verification:
  - `cd apps/web && npm run typecheck`: passed.
  - `cd apps/web && npm test`: 19 files / 45 tests passed.
  - `cd apps/web && npm run build`: passed after final component extraction and copy cleanup.
  - Local production server `http://127.0.0.1:13003` with EC2 FastAPI tunnel `127.0.0.1:8787`.
  - `STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`: 69/69 passed after final component extraction and copy cleanup, including `/cycle-map` mobile/tablet/desktop internal-copy gate.
  - `/cycle-map` visual text smoke against `http://127.0.0.1:13003`: desktop/tablet/mobile all `hasBanned=false`, `horizontalOverflow=false`.
  - Screenshot evidence:
    - `/tmp/stockanalysis-visual-qa/cycle-map-desktop.png`
    - `/tmp/stockanalysis-visual-qa/cycle-map-tablet.png`
    - `/tmp/stockanalysis-visual-qa/cycle-map-mobile.png`
  - `git diff --check`: passed.
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
  - `bash scripts/verify_frontend_api_contract.sh`: passed.
  - `bash scripts/verify_project_execution_roadmap.sh`: passed.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operations-ai-cyclemap-quality-v1`: passed.
- EC2 service smoke:
  - `systemctl is-active stockanalysis-web.service stockanalysis-web-public-13000.service stockanalysis-frontend-api.service`: all active.
  - `http://127.0.0.1:8787/__ready`: 200, `ready_time=0.003947`.
  - `http://127.0.0.1:13000/`: 200, `web13000_time=1.713448`.
- EC2 deploy and production build recovery:
  - `develop` was pushed at commit `87f9b3c7` and EC2 `/opt/stockanalysis/app` fast-forwarded to the same commit.
  - First EC2 Next build was interrupted and left `.next` without `BUILD_ID`, causing `stockanalysis-web*` services to restart with `production-start-no-build-id`.
  - Fixed by stopping `stockanalysis-web.service` and `stockanalysis-web-public-13000.service`, removing incomplete `.next`, running `NEXT_TELEMETRY_DISABLED=1 npm run build`, then restarting web/API services.
  - Post-recovery EC2 smoke: `stockanalysis-web.service`, `stockanalysis-web-public-13000.service`, `stockanalysis-frontend-api.service` all `active`; `http://127.0.0.1:8787/__ready` 200; `http://127.0.0.1:3000/` 200; `http://127.0.0.1:13000/` 200; `http://127.0.0.1:13000/cycle-map` 200.
- EC2 Codex OAuth relogin and AI smoke recovery:
  - Root cause after deployment was a revoked EC2 Codex OAuth refresh token; `news-rss-translation-run` and `news-rss-ai-extract-run` failed with `token_invalidated` / `refresh_token_invalidated`.
  - Browser-side prerequisite was enabling `ChatGPT > Settings > Security > Codex용 장치 코드 인증 활성화`.
  - New device code `HBGP-ITM5R` was submitted at `https://auth.openai.com/codex/device`; browser confirmed `Codex에 로그인됨`.
  - `GET /__admin/codex-oauth/status` then reported `status=healthy`, `login_probe_status=logged_in`, `login_probe_message="Logged in using ChatGPT"`, `order_boundary=read_only_no_order`.
  - `POST /__admin/codex-oauth/smoke/direct` succeeded at `2026-07-01T04:39:03Z`.
  - `news-rss-translation-run --provider codex_oauth --limit 1 --execute` completed with `run_id=8798`, `invocation_id=12636`, `failed_document_count=0`.
  - `news-rss-ai-extract-run --provider codex_oauth --limit 1 --execute` completed with `run_id=8799`, `invocation_id=12637`, `status=inserted_validated`, `validated_theme_impact_count=2`, `validated_instrument_impact_count=1`, `failed_candidate_count=0`.
  - `/api/data-health.live_ai_invocation_health.status=recovered_with_recent_failures`, `attention_required=false`, `critical_latest_unhealthy_count=0`; old failed invocations remain as audit history.
- Local tunnel smoke:
  - A fresh SSH tunnel to EC2 was opened for `127.0.0.1:13000` and `127.0.0.1:8787`.
  - Local `http://127.0.0.1:13000/`: 200.
  - Local `http://127.0.0.1:13000/data-health`: 200.

## Performance Baseline

Measured against local production Next server `http://127.0.0.1:13003` using EC2 FastAPI tunnel:

| Route | Status | time_total |
| --- | ---: | ---: |
| `/` | 200 | 2.546896s |
| `/market-map` | 200 | 0.515278s |
| `/cycle-map` | 200 | 0.510357s |
| `/stocks/AAPL` | 200 | 1.066721s |
| `/recommendations/AAPL-professional-2026-06-25` | 200 | 0.484777s |
| `/data-health` | 200 | 1.641536s |

Build baseline:

- `next build`: compiled successfully in `1200ms`; TypeScript finished in `3.7s`.

## Safety Boundary

- Recommendation weights are unchanged.
- Broker submit remains out of scope.
- Failed AI invocation history must remain auditable.
- No DB schema, benchmark, portfolio position, recommendation score, or broker order boundary changed in this task.

## Remaining Work

- The code commit has been merged/pushed to `develop` and deployed to EC2.
- AI invocation health is recovered, but `overall_status=attention_required` remains because of managed review/outcome gates:
  - `benchmark_drift_quality_attention`
  - `portfolio_review_decision_history_attention`
  - `portfolio_review_feedback_calibration_attention`
  - `portfolio_review_feedback_cadence_attention`
  - `recommendation_outcome_calibration_attention`
  - `recommendation_outcome_maturity_attention`
- Do not hide these gates. They require more outcome data or explicit review tasks, not UI suppression.
