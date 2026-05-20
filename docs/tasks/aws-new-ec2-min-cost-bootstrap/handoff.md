# Session Handoff

## Active Task

- 이름: aws-new-ec2-min-cost-bootstrap
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - AWS Console 계정 `wooody (115623963546)`, 리전 `us-east-1` 확인.
  - 기존 EC2 `settleLab` 재사용이 아니라 새 EC2 launch form으로 전환.
  - task contract 작성.
  - 사용자가 새 EC2를 생성했고 Codex가 접속/런타임 bootstrap을 완료했다.
  - 생성/접속 확인된 EC2:
    - Name: `stockanalysis-mvp-20260520`
    - Instance ID: `i-029d51b163fb07b61`
    - Public IPv4: `98.86.164.57`
    - Private IPv4: `172.31.9.2`
    - AMI/OS: Amazon Linux 2023.11
    - Instance type: `t3.small`, 2 vCPU, 2 GiB
    - Key pair: existing `settle`
    - Private key used locally: `/Users/woody/Downloads/settle.pem`
    - Security group: `sg-0a2d52009e73a59e3` (`stockanalysis-mvp-ssh-20260520`)
    - SSH inbound: `211.54.17.177/32` and AWS EC2 Instance Connect `18.206.107.24/29`
    - HTTP/HTTPS inbound: not enabled
    - Storage: gp3 16 GiB
  - GitHub 최신화:
    - Branch: `codex/local-mvp-runtime-aws-bootstrap`
    - Commit: `c1dde92`
    - Draft PR: `https://github.com/gwkim92/stockA/pull/20`
  - EC2 runtime:
    - Repo clone: `/opt/stockanalysis/app`
    - Runtime/env files: `/opt/stockanalysis/runtime/` with `0600` env files
    - Python venv: `/opt/stockanalysis/venv` using Python 3.12
    - Postgres: Docker `postgres:16-alpine`, container `stockanalysis-postgres`, bound to `127.0.0.1:5432`, `--restart unless-stopped`
    - FastAPI: `stockanalysis-frontend-api.service`, bound to `127.0.0.1:8787`
    - Next.js: `stockanalysis-web.service`, bound to `127.0.0.1:3000`
    - Local SSH tunnel from this workstation: `127.0.0.1:13000 -> EC2 127.0.0.1:3000`, `127.0.0.1:18787 -> EC2 127.0.0.1:8787`
  - EC2 data ingest smoke:
    - Data operations env: `/opt/stockanalysis/runtime/data-operations.env`
    - Provider secret import: `/opt/stockanalysis/runtime/provider-secrets.env`
    - Watchlist: `/opt/stockanalysis/runtime/market-price-watchlist.csv`
    - RSS feed config: `/opt/stockanalysis/runtime/news-rss-feeds.json`
    - Worker report: `/opt/stockanalysis/runtime/local-ingest-worker.json`
    - Manual smoke report: `/opt/stockanalysis/runtime/manual-local-ingest-smoke.json`
    - `market-universe-bootstrap`: succeeded, 7,558 instruments selected.
    - `local-ingest-worker-run --execute`: completed with `market-price-daily`, `news-rss-daily`, `event-intelligence-weekly` all succeeded.
    - Additional `news-rss-enrich-run`: completed, 20 news events enriched.
    - Additional `news-rss-cluster-evidence-run`: completed, 3 local-rule AI evidence artifacts inserted.
  - 2026-05-20 runtime health follow-up:
    - User-facing production Server Components error was traced to authorized FastAPI `GET /api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01` returning `500`.
    - Root cause: EC2 DB has no `portfolio.portfolio`/`portfolio.position_snapshot` rows yet, while `/intelligence` was still requesting a fixed historical portfolio coverage date.
    - Fix: live portfolio coverage now returns a stable empty DTO with `missing_position_snapshot:<portfolio>` instead of throwing, and `/intelligence` requests the latest `portfolio.position_snapshot` freshness date from `/api/data-health` when available.
  - 2026-05-20 operating-data follow-up:
    - Added a one-symbol TSLA Twelve Data backfill through the existing free provider budget ledger because live news/event impacts were attached to TSLA and the prior watchlist did not include TSLA.
    - Ran the 2026-05-20 signal chain against live EC2 Postgres: `strategy-universe-slice`, `market-feature-snapshot`, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `thesis-bootstrap`, and `thesis-review-bootstrap`.
    - Signal state now has `cycle_state_snapshot=2`, `recommendation=1`, `investment_thesis=1`, `thesis_review=1`. The generated recommendation is TSLA with an exclude/exit-style paper action.
    - Rebuilt `/opt/stockanalysis/runtime/portfolio-positions.csv` from latest DB prices for AAPL, MSFT, NVDA, and TSLA, then ran `portfolio-position-daily` and `portfolio-remediation-daily`.
    - Portfolio state now has `portfolio.position_snapshot=4`, `portfolio.review=1`, `portfolio.remediation_ticket=4`; tickets are 3 thesis-remediation items for AAPL/MSFT/NVDA and 1 outcome-remediation item for TSLA.
    - Ran `macro-weekly` for CPIAUCSL/FEDFUNDS from 2025-01-01 and `performance-outcome-monthly`; outcome scheduler succeeded with no due candidates because the newly generated 2026-05-20 long-term recommendation has not reached an outcome horizon yet.
    - Ran paper safety bootstrap and paper validation audit without broker submission. Trading readiness now has broker/account/order-limit/audit gates passing, but remains blocked by the global kill switch and failed paper validation. `submitted_to_broker_count=0`.
- 막힌 점/보류:
  - 로컬 AWS CLI profile은 AWS Console 계정과 다르므로 AWS CLI로는 이 계정 리소스를 변경하지 않음.
  - HTTP/HTTPS security group은 아직 열지 않았다. 현재 접속은 SSH tunnel 전용이다.
  - 실제 recurring data ingest scheduler/timer는 아직 서버에서 활성화하지 않았다.
  - EC2 `systemctl list-timers --all | grep -i stockanalysis` returns no stockanalysis timers. Current server state is service runtime plus manual data operations, not recurring automation.
  - EC2 Codex OAuth setup completed after user device login:
    - `/usr/bin/codex`, `codex-cli 0.132.0`
    - `codex login status`: `Logged in using ChatGPT`
    - `scripts/check_data_operations_runtime_env.sh --env-file /opt/stockanalysis/runtime/data-operations.env`: passed
    - `event-intelligence-llm-extract --provider codex_oauth` succeeded for SEC document `0000320193-24-000123`.
  - 브로커/실거래 연결은 아직 연결하지 않았다.

## Exact Next Step

- SSH tunnel을 유지한 상태에서 `http://127.0.0.1:13000`으로 cockpit 화면을 확인한다.
- 서버 내부에서 data operations env를 별도로 구성하고, 단발 ingest smoke를 실행해 `/api/data-health` run history에 반영되는지 검증한다.
- 그 다음 `systemd` timer 기반 서버 scheduler를 설계/적용한다. Mac LaunchAgents/`launchctl`은 계속 사용하지 않는다.
- 외부 공개가 필요하면 HTTPS/reverse proxy와 security group HTTP/HTTPS 개방을 별도 task로 처리한다.

## Verification Evidence

- EC2 package/runtime:
  - `git version 2.50.1`
  - `Python 3.12.13`
  - `node v22.22.2`, `npm 10.9.7`
  - `Docker 25.0.14`
- GitHub:
  - local branch pushed to `origin/codex/local-mvp-runtime-aws-bootstrap`
  - draft PR created: `https://github.com/gwkim92/stockA/pull/20`
- Local repo before EC2 deploy:
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`: `Ran 656 tests ... OK`
  - `npm run typecheck`: passed
  - `npm run build`: passed
  - `bash scripts/verify_project_execution_roadmap.sh`: passed
  - `bash scripts/verify_local_ai_pipeline_run_alignment.sh`: passed
- EC2 runtime:
  - DB migrations/seeds applied; non-system DB table count: `51`
  - `scripts/check_frontend_api_server_runtime_env.sh --env-file /opt/stockanalysis/runtime/frontend-api.env`: passed
  - FastAPI `/__ready`: `status=ok`
  - authorized `/api/dashboard/today`: DTO keys include `contract_version,data,generated_at,links`
  - Next routes `/`, `/data-health`, `/cycles`, `/events`, `/stocks`, `/intelligence`, `/paper-trading`, `/trading-readiness`: all returned `200`
  - `stockanalysis-frontend-api.service`: `active`
  - `stockanalysis-web.service`: `active`
  - EC2 data:
  - `ref.instrument`: `7,558`
  - `market.daily_price_bar`: `600`
  - `ingest.source_document`: `20`
  - `event.event`: `20`
  - `event.event_classification_impact`: `20`
  - `event.event_instrument_impact`: `2`
  - `ai.extraction_artifact`: `3`
  - `ai.model_invocation`: `3`
  - `ops.pipeline_run`: `13`
  - authorized `/api/data-health`: `manual_local_ingest_smoke.status=passed`, `local_ingest_worker.status=completed`
  - authorized `/api/stocks`: `stock_count=6`, `priced_stock_count=6`, `latest_price_date=2026-05-19`
  - authorized `/api/ai/news-clusters?asOfDate=2026-05-20&limit=4`: `cluster_count=3`, first evidence `ai-evidence-3`, first theme `AI_SEMICONDUCTOR_CYCLE`
  - local tunnel `/intelligence`: returned `200`
  - EC2 Codex OAuth:
    - `codex_oauth_invocations`: `1`
    - `event_intelligence_runs`: `2`
    - `structured_artifacts`: `1`
    - `sec_events`: `1`
    - authorized `/api/data-health`: latest `event-intelligence-weekly` is `pipeline-run-16`, `succeeded`
  - 2026-05-20 runtime health follow-up:
    - Before fix, direct authorized API call returned `500` for `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01`.
    - Services checked on EC2: `stockanalysis-frontend-api.service=active`, `stockanalysis-web.service=active`, Docker `stockanalysis-postgres=Up`.
    - Timers checked on EC2: no stockanalysis systemd timer installed.
    - Data-health checked on EC2: market/news/SEC/AI jobs are `ok`; portfolio-position, portfolio-remediation, performance outcome, attribution, macro, and cycle/recommendation jobs are still `missing`.
    - Deployed commit `fb6270c` to EC2, rebuilt Next, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`; both returned `active`.
    - After deploy, authorized EC2 API `GET /api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-20` returned HTTP `200`, `position_count=0`, and `blocking_reasons=['missing_position_snapshot:Long Term Paper']`.
    - After deploy, local tunnel routes `/`, `/data-health`, `/cycles`, `/events`, `/stocks`, `/intelligence`, `/paper-trading`, `/trading-readiness`, `/performance`, `/portfolio/coverage`, `/remediation` all returned HTTP `200`.
    - After deploy, `/intelligence` HTML no longer contained `투자 운영 데이터를 불러오지 못했다`, `Server Components render`, `digest`, or `FrontendApiError`.
    - Current EC2 DB counts after Codex OAuth smoke and runtime fix: `ref.instrument=7558`, `market.daily_price_bar=600`, `ingest.source_document=22`, `event.event=21`, `event.event_instrument_impact=2`, `ai.extraction_artifact=4`, `ai.model_invocation=4`, `ops.pipeline_run=16`, `portfolio.position_snapshot=0`.
    - 2026-05-20 operating-data follow-up:
      - `/api/data-health`: all jobs except `portfolio-attribution-monthly` are `ok`; remaining overall status is `attention_required`.
      - `/api/data-health` provider budget: Twelve Data `used_request_count=7`, `remaining_request_count=17` for budget date `2026-05-20`.
      - DB counts: `macro.observation=31`, `signal.cycle_state_snapshot=2`, `signal.recommendation=1`, `signal.investment_thesis=1`, `signal.thesis_review=1`, `portfolio.position_snapshot=4`, `portfolio.review=1`, `portfolio.remediation_ticket=4`, `trading.paper_validation_run=1`, `trading.order_intent_audit=1`, `performance.thesis_outcome=0`, `performance.attribution_run=0`.
      - `/api/trading/readiness`: `readiness_status=blocked`, gates `broker_boundary/account_permission/order_limit_policy/audit_log=pass`, `kill_switch/paper_validation=blocked`, `submitted_to_broker_count=0`.
      - Local tunnel route smoke returned HTTP `200` for `/data-health`, `/intelligence`, `/paper-trading`, `/trading-readiness`, `/portfolio/coverage`, `/remediation`, `/stocks`, `/recommendations/recommendation-1`, and `/theses/thesis-1`.
      - EC2 logs checked for the last 10 minutes: no FastAPI `500`, `Traceback`, `ERROR`, Next `FrontendApiError`, `digest`, or `500` entries.
      - Services remain active: `stockanalysis-frontend-api.service=active`, `stockanalysis-web.service=active`; no `stockanalysis` systemd timer is installed.
    - Focused local verification after code fix:
      - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_server -v`: `Ran 54 tests ... OK`
      - `cd apps/web && npm run typecheck`: passed
      - `cd apps/web && npm run build`: passed
      - `git diff --check`: passed

## Cost Notes

- Console displays `t3.small` and AMI as Free Tier available, but Free Tier/credit eligibility depends on account terms and usage.
- Public IPv4 can be billed separately even when EC2 compute is free-tier eligible.
- 16 GiB gp3 is within the common 30 GiB EBS Free Tier storage note, but actual account eligibility must be watched in Billing.

## Risks

- Existing `settle` private key is not present in local `~/.ssh`; EC2 Instance Connect should be used first.
- If EC2 Instance Connect fails, access may require the user's `settle` private key or a new/imported key pair.
- Single EC2 with local Postgres is the lowest-cost MVP path, not HA/production-grade.
- The EC2 runtime currently proves read-only cockpit plus manual ingest/signal/portfolio/paper-validation operation. It does not yet prove full recurring automation because scheduler timers are still not installed. Portfolio attribution is not populated yet because no long-term outcome horizon has matured for the new 2026-05-20 recommendation.
