# Session Handoff

## Active Task

- 이름: local-live-mvp-runtime
- 담당: Codex
- 날짜: 2026-05-16

## Current Status

- 완료:
  - task contract and plan created.
  - Python 3.13 venv created at `/private/tmp/stockanalysis-runtime/venv`.
  - editable project dependencies installed with `.[otel]`.
  - repo-outside local fixture env files created and chmod 600.
  - repo-outside data operations env now includes the local-only legacy `STOCKANALYSIS_PSQL_COMMAND` required by the current ingest CLI boundary.
  - scheduler activation request command preview now uses `$HOME/Library/LaunchAgents/...` instead of quoted `~/Library/LaunchAgents/...`.
  - Docker Postgres container `stockanalysis-local-postgres` is running on `127.0.0.1:55432`.
  - migrations and seeds were applied to the local Postgres runtime.
  - one-shot `macro-weekly` data operations smoke succeeded and wrote artifacts under `/private/tmp/stockanalysis-runtime/artifacts`.
  - persistent local DB fixture bootstrap loaded market, SEC, event, theme, cycle, recommendation, thesis, performance, portfolio, attribution, and remediation data.
  - FastAPI read-only backend is running at `http://127.0.0.1:8787` with live Postgres readiness passing.
  - Next.js cockpit is running at `http://127.0.0.1:3001`; port 3000 is occupied by an unrelated `llm-wiki` Next server.
  - frontend typecheck/build passed.
  - activation request, manual approval, manual preflight, and roadmap verification passed.
  - 2026-05-17 update: root `.env` remains git-ignored and now includes `STOCKANALYSIS_SEC_USER_AGENT` with `wooody.public@gmail.com`.
  - 2026-05-17 update: `/private/tmp/stockanalysis-runtime/data-operations.real.env` was generated from root `.env` plus local runtime defaults.
  - 2026-05-17 update: FRED provider smoke passed for `CPIAUCSL`.
  - 2026-05-17 update: real FRED `macro-weekly` ingest passed for `CPIAUCSL` and `FEDFUNDS` from `2025-01-01`.
  - 2026-05-17 update: SEC AAPL submissions upsert passed for CIK `0000320193`, max 3 filings, latest filing date `2026-05-12`.
  - 2026-05-17 update: FastAPI `/api/data-health` and `/api/events?asOfDate=2026-05-17` returned HTTP 200 after real-provider ingest.
  - 2026-05-17 update: Alpha Vantage market price ingest no longer defaults to the premium `TIME_SERIES_DAILY_ADJUSTED` endpoint; default mode is now free `TIME_SERIES_DAILY`.
  - 2026-05-17 update: real AAPL market-price upsert passed with 100 free daily bars, latest trade date `2026-05-15`, `price_adjustment_mode=unadjusted_fallback`, run_id `29`.
  - 2026-05-17 update: Codex OAuth LLM provider was added for offline data operations jobs and real `event-intelligence-llm-extract --provider codex_oauth` smoke passed with run_id `33`.
  - 2026-05-17 update: free-tier market backfill throttling was added; real capped batch smoke loaded AAPL through run_id `34` and skipped MSFT by request budget without consuming a second provider call.
  - 2026-05-17 update: local free-tier provider budget ledger was added through `stockanalysis-operations market-price-free-backfill-run`; no-quota smoke consumed zero Alpha Vantage calls.
  - 2026-05-17 update: `/api/data-health` and `/data-health` now expose sanitized free-tier provider budget status from the local ledger.
  - 2026-05-17 update: positive-budget Alpha Vantage run consumed 1 provider call and recorded it in the local ledger, but MSFT price write failed because no canonical instrument exists for `MSFT`.
  - 2026-05-17 update: Next.js cockpit static UI and common status/action/reason labels were localized to Korean.
  - 2026-05-17 update: live SEC market universe bootstrap succeeded through `market-universe-weekly`, loaded 7,562 active canonical instruments, and `MSFT`/`NVDA`/`AAPL` now resolve for price upsert.
  - 2026-05-17 update: FastAPI and Next.js were restarted locally. `/__health`, protected `/api/data-health`, `/`, and `/data-health` returned HTTP 200.
  - 2026-05-17 update: Alpha Vantage local budget ledger was corrected from a conservative one-call smoke budget to the official free-tier cap assumption of 25 calls/day without making a provider request. Local ledger now shows `used=1`, `remaining=24`.
  - 2026-05-17 update: free market data provider strategy was documented. Alpha Vantage remains a small-priority fallback; Twelve Data is the first no-cost broad-market pilot candidate.
  - 2026-05-17 update: Twelve Data provider adapter pilot added fixture-backed `time_series_daily` normalization, provider-aware market price CLI/upsert/free-backfill propagation, provider alias normalization, and data-health provider-budget selection via `STOCKANALYSIS_MARKET_PRICE_PROVIDER`.
  - 2026-05-17 update: live Twelve Data AAPL smoke succeeded through the operations free-backfill runner, inserted 100 daily bars through run_id `36`, and updated `/private/tmp/stockanalysis-runtime/twelve-data-budget-ledger.json` to `used=1`, `remaining=799`.
  - 2026-05-17 update: FastAPI was restarted with Twelve Data provider budget env; authorized `/api/data-health` returned provider `twelve_data`, status `configured`, and remaining budget `799`.
  - 2026-05-17 update: Twelve Data small priority watchlist expansion succeeded for `MSFT`, `NVDA`, `GOOGL`, and `AMZN`, inserting 400 bars across run_id `37` through `40` and moving local Twelve budget to `used=5`, `remaining=795`.
  - 2026-05-17 update: DB verification confirmed `AAPL`, `MSFT`, `NVDA`, `GOOGL`, and `AMZN` all have `market.daily_price_bar` data through `2026-05-15`.
  - 2026-05-18 update: freshness-aware duplicate-call avoidance was added behind `--skip-if-fresh` and `--freshness-date`; local DB smoke skipped the first five Twelve Data symbols with `provider_request_count=0`.
  - 2026-05-18 update: frontend live evidence linking was fixed. Event rows now inherit source-document instrument/theme fallback, document-scoped AI artifacts link as `ai-evidence-1`, and browser smoke confirmed `/events`, source document detail, and AI evidence detail render connected AAPL evidence instead of `UNKNOWN/UNCLASSIFIED`.
  - 2026-05-18 update: Twelve Data expanded watchlist was created outside the repo at `/private/tmp/stockanalysis-runtime/watchlists/twelve-data-expanded-watchlist.csv`.
  - 2026-05-18 update: Twelve Data expanded watchlist first capped run loaded `META`, `TSLA`, `JPM`, `UNH`, `XOM`, `AVGO`, `LLY`, `COST`, `WMT`, and `HD` with 100 daily bars each through `2026-05-15`.
  - 2026-05-18 update: Twelve Data expanded watchlist second capped run skipped those ten as fresh and loaded `PG`, `KO`, `PEP`, `CRM`, `ORCL`, `AMD`, `INTC`, `NFLX`, `DIS`, and `BAC` with 100 daily bars each through `2026-05-15`.
  - 2026-05-18 update: repeat expanded watchlist run confirmed duplicate-call avoidance for all 20 expanded symbols with `provider_request_count=0`.
  - 2026-05-18 update: local DB now has 25 market price symbols fresh through `2026-05-15`: the original five priority names plus twenty expanded watchlist names.
  - 2026-05-18 update: market-price scheduler defaults now use `stockanalysis-operations market-price-daily-run --skip-if-fresh`, repo-outside expanded Twelve Data watchlist/ledger env, and scheduler run date as default freshness date.
  - 2026-05-18 update: scheduler boundary local run for `market-price-daily` succeeded with all expanded symbols skipped as fresh and `provider_request_count=0`.
  - 2026-05-18 update: `market-price-daily` scheduler activation operator dry-run evidence was generated under `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily` using `market-price-daily-run --skip-if-fresh`; pending approval gate remains blocked until a real approval record exists.
  - 2026-05-18 update: `/api/data-health` and `/data-health` now expose sanitized scheduler activation state from the repo-outside pending approval gate report. The local page shows `market-price-daily` as `수동 승인 대기` and `activation_allowed=false`.
  - 2026-05-19 update: `/api/data-health` stale/missing operations were remediated with scheduler-free `stockanalysis-operations run` executions. `portfolio-position-daily`, `portfolio-remediation-daily`, and `performance-outcome-monthly` now report `ok`; overall data health is `healthy`.
  - 2026-05-19 update: repo-outside `/private/tmp/stockanalysis-runtime/positions.local-fixture.csv` was repaired to include required `market_price` and `market_value` columns, using canonical AAPL close `300.230010` from `2026-05-15`.
  - 2026-05-19 update: Next.js dev server was restarted on `http://127.0.0.1:3001`; Chrome UI smoke confirmed `/data-health` renders Korean status `정상`, failure count `0`, and updated pipeline rows.
  - 2026-05-19 update: scheduler-free `market-price-daily` rollover run loaded the expanded Twelve Data watchlist through latest trade date `2026-05-18`, consumed 20 provider calls for budget date `2026-05-19`, and moved provider budget to `780/800`.
  - 2026-05-19 update: `/data-health` budget ratio wrapping was fixed so `780 / 800` renders on one line.
  - 2026-05-19 update: market-price daily freshness default now uses `latest_completed_us_market_day` instead of raw run date. A zero-call local smoke without `--freshness-date` resolved target `2026-05-18`, skipped all 20 fresh symbols, and preserved Twelve Data budget at `780/800`.
- 진행 중:
  - decide whether the no-cost unadjusted daily price policy is sufficient for recommendation/performance quality or whether a free adjusted-price provider is still needed.
  - decide the next local MVP slice: improve operations visibility/data-health gaps or prepare a real scheduler approval packet for manual operator review.
- 막힌 점:
  - Alpha Vantage `daily_adjusted` provider smoke returned `Information: premium endpoint`, so current free key cannot provide split/dividend-adjusted prices through that endpoint.
  - OpenAI API runtime still requires an API key for direct `api.openai.com` calls; Codex/ChatGPT OAuth is now supported only through a local `codex exec` job boundary.
  - production data-provider credentials, recurring scheduler activation, deployment manifests, paper trading, and real trading remain outside this slice.

## Runtime Paths

- runtime kit: `/private/tmp/stockanalysis-runtime`
- Python venv: `/private/tmp/stockanalysis-runtime/venv`
- frontend API env: `/private/tmp/stockanalysis-runtime/frontend-api.env`
- data operations env: `/private/tmp/stockanalysis-runtime/data-operations.env`
- real data operations env: `/private/tmp/stockanalysis-runtime/data-operations.real.env`
- local Postgres container: `stockanalysis-local-postgres`
- FastAPI URL: `http://127.0.0.1:8787`
- Next.js URL: `http://127.0.0.1:3001`

## Decisions

- Python 3.13을 기준 runtime으로 사용한다.
- actual host scheduler activation은 이 task 범위 밖이다.
- real provider key가 없으면 fixture provider + real/local DB smoke를 먼저 목표로 한다.

## Verification

- Passed:
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -c "import fastapi, uvicorn, psycopg, httpx"`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python scripts/check_frontend_api_server_runtime_env.sh --env-file /private/tmp/stockanalysis-runtime/frontend-api.env`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.env`
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_scheduler_activation_request -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_runtime_smoke.sh`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python scripts/smoke_data_operations_runtime.sh --env-file /private/tmp/stockanalysis-runtime/data-operations.env --job-id macro-weekly --timeout-seconds 120 -- /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.ingest.cli macro-batch-upsert --fixtures-dir tests/fixtures --series-id CPIAUCSL --series-id FEDFUNDS`
  - persistent local DB fixture bootstrap command completed.
  - FastAPI live smoke passed for `/__health`, `/__ready`, unauthorized `/api/dashboard/today`, authorized `/__endpoints`, `/api/dashboard/today`, `/api/data-health`, `/api/cycles`, `/api/events`, `/api/recommendations/AAPL-2024-11-01`.
  - Next live route smoke passed for `/`, `/data-health`, `/cycles`, `/events`, `/recommendations/AAPL-2024-11-01`.
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_live_scheduler_activation_request.sh`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_manual_host_scheduler_activation_preflight.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - FRED provider smoke: `stockanalysis.ingest.cli fetch fred series --param series_id=CPIAUCSL`
  - real macro ingest smoke: `scripts/smoke_data_operations_runtime.sh --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env --job-id macro-weekly -- ... macro-batch-upsert --series-id CPIAUCSL --series-id FEDFUNDS --observation-start 2025-01-01`
  - SEC real metadata upsert: `stockanalysis.ingest.cli sec-filings-upsert --cik 320193 --max-filings 3`
  - Alpha Vantage free market price upsert: `STOCKANALYSIS_ALPHA_VANTAGE_PRICE_MODE=daily stockanalysis.ingest.cli market-price-upsert --symbol AAPL --outputsize compact`
  - Codex OAuth AI smoke: `stockanalysis.ingest.cli event-intelligence-llm-extract --external-document-id 0000320193-24-000123 --provider codex_oauth --model-name codex-cli-default --reasoning-effort low --max-input-chars 1800 --min-confidence 0.5`
  - Alpha Vantage capped batch smoke: `STOCKANALYSIS_ALPHA_VANTAGE_PRICE_MODE=daily stockanalysis.ingest.cli market-price-batch-upsert --symbol AAPL --symbol MSFT --outputsize compact --throttle-seconds 1 --max-requests-per-run 1`
  - Alpha Vantage no-quota free backfill runner smoke: `stockanalysis-operations market-price-free-backfill-run --watchlist /private/tmp/stockanalysis-runtime/watchlists/free-market-watchlist.csv --ledger /private/tmp/stockanalysis-runtime/alpha-vantage-budget-ledger.json --daily-budget 1 --max-requests-per-run 0 --throttle-seconds 1 --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - Provider budget API smoke: authorized `GET http://127.0.0.1:8787/api/data-health` returned `data.provider_budget.status=configured`, `remaining_request_count=1`, `provider_request_count=0`.
  - Provider budget frontend smoke: `GET http://127.0.0.1:3001/data-health` returned HTTP `200` and rendered `Free Provider Budget`.
  - Positive-budget Alpha Vantage run: `stockanalysis-operations market-price-free-backfill-run --watchlist /private/tmp/stockanalysis-runtime/watchlists/free-market-positive-watchlist.csv --ledger /private/tmp/stockanalysis-runtime/alpha-vantage-budget-ledger.json --daily-budget 1 --max-requests-per-run 1 --throttle-seconds 1 --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env` consumed `provider_request_count=1`, failed `MSFT` with `No canonical instrument found for symbol 'MSFT'`, skipped `NVDA`/`AAPL`, and left the conservative smoke budget exhausted.
  - Korean frontend typecheck/build: `cd apps/web && npm run typecheck`, `cd apps/web && npm run build`.
  - Korean local route smoke: `GET /`, `/data-health`, `/remediation`, `/performance`, `/themes/ANNUAL_REPORTING`, `/ai-evidence/sec-event-aapl-10k-20240928` returned HTTP `200`.
  - FastAPI read smoke: `/api/data-health`, `/api/events?asOfDate=2026-05-17`
  - Live SEC universe bootstrap: `market-universe-weekly` artifact run passed, selected 7,562 Nasdaq/NYSE records, latest `market_universe_bootstrap` run status is `succeeded`.
  - Canonical instrument lookup: `MSFT`, `NVDA`, and `AAPL` resolve through `resolve_instrument_for_symbol`.
  - FastAPI restart smoke: `GET /__health` and authorized `GET /api/data-health` returned HTTP `200`.
  - Next restart smoke: `GET /` and `/data-health` returned HTTP `200`, rendered Korean labels, and showed Alpha Vantage local provider budget `24/25`.
  - Alpha Vantage budget correction smoke: `stockanalysis-operations market-price-free-backfill-run --daily-budget 25 --max-requests-per-run 0 ...` consumed `provider_request_count=0` and updated the local ledger to `used=1`, `remaining=24`.
  - Twelve Data live smoke: `stockanalysis-operations market-price-free-backfill-run --provider twelve_data --daily-budget 800 --max-requests-per-run 1 --outputsize 100 ...` consumed `provider_request_count=1`, loaded AAPL 100 bars, and left local Twelve budget `remaining=799`.
  - Twelve Data provider budget API smoke: authorized `GET http://127.0.0.1:8787/api/data-health` returned `provider=twelve_data`, `status=configured`, `used_request_count=1`, `remaining_request_count=799`.
  - Twelve Data provider budget frontend smoke: `GET http://127.0.0.1:3001/data-health` returned HTTP `200` and rendered the remaining budget count.
  - Twelve Data small priority watchlist smoke: `stockanalysis-operations market-price-free-backfill-run --provider twelve_data --daily-budget 800 --max-requests-per-run 4 --outputsize 100 ...` consumed `provider_request_count=4`, loaded `MSFT`/`NVDA`/`GOOGL`/`AMZN` 100 bars each, and left local Twelve budget `remaining=795`.
  - Twelve Data DB verification: `AAPL`, `MSFT`, `NVDA`, `GOOGL`, and `AMZN` all have latest `market.daily_price_bar.trade_date=2026-05-15`.
  - Twelve Data freshness skip smoke: `stockanalysis-operations market-price-free-backfill-run --provider twelve_data --max-requests-per-run 5 --skip-if-fresh --freshness-date 2026-05-15 ...` skipped `AAPL`/`MSFT`/`NVDA`/`GOOGL`/`AMZN` with `provider_request_count=0`.
  - Frontend live evidence linking focused tests: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`.
  - Frontend live evidence browser smoke: `/events`, `/source-documents/source-document-0000320193-24-000123`, and `/ai-evidence/ai-evidence-1` rendered linked AAPL evidence.
  - Twelve Data expanded watchlist run 1: 10 succeeded, 10 skipped by request cap, `provider_request_count=10`, ledger moved to `used=10`, `remaining=790` for `2026-05-18`.
  - Twelve Data expanded watchlist run 2: 10 fresh skips, 10 succeeded, `provider_request_count=10`, ledger moved to `used=20`, `remaining=780` for `2026-05-18`.
  - Twelve Data expanded watchlist repeat skip: 20 fresh skips, `provider_request_count=0`, ledger remained `used=20`, `remaining=780`.
  - DB verification: 25 canonical symbols have daily price bars through `2026-05-15`; expanded symbols have 100 bars each.
  - Data health API/browser verification: `/api/data-health` and `/data-health` show Twelve Data budget `780/800` remaining and `20` used.
  - Market price scheduler defaults focused tests: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_cadence tests.test_data_operations_env_readiness tests.test_data_operations_cli tests.test_data_operations_scheduler_boundary tests.test_market_price_free_backfill tests.test_ingest_cli.IngestCliTests.test_data_operations_env_readiness_cli_prints_redacted_report`.
  - Market price scheduler boundary preflight: `market-price-daily` passed with required env groups `database` and `market_price_provider`.
  - Market price scheduler boundary local run: artifact `/private/tmp/stockanalysis-runtime/artifacts/20260518T080222Z_market-price-daily/stdout.json` recorded 20 fresh skips and `provider_request_count=0`.
  - Market price scheduler activation operator dry-run: `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/operator-dry-run/evidence/operator-dry-run.json` recorded `job_id=market-price-daily`, `scheduler_activation=not_installed`, `launchctl_executed=false`, and `child_command_executed=false`.
  - Market price scheduler pending approval gate: `/private/tmp/stockanalysis-runtime/evidence/activation-chain-market-price-daily/pending-approval-gate.json` recorded `approval_gate=blocked_pending_manual_approval` and `activation_allowed=false`.
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_runtime_env_readiness.sh`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_scheduler_activation_runbook.sh`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_scheduler_operator_dry_run.sh`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
  - Data-health scheduler activation focused tests: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - Data-health frontend checks: `cd apps/web && npm run typecheck`, `cd apps/web && npm run build`.
  - Data-health browser smoke: `http://localhost:3001/data-health` rendered `스케줄러 승인`, `수동 승인 대기`, and `market-price-daily`.
  - Data-health stale remediation before API check: authorized `GET /api/data-health` returned `attention_required` with stale `portfolio-position-daily`, stale `portfolio-remediation-daily`, and missing `performance-outcome-monthly`.
  - Data-health stale remediation runs:
    - `portfolio-position-daily` artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001357Z_portfolio-position-daily/stdout.json`, run_id `61`.
    - `portfolio-remediation-daily` artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001436Z_portfolio-remediation-daily/stdout.json`, run_id `62`.
    - `performance-outcome-monthly` artifact `/private/tmp/stockanalysis-runtime/artifacts/20260519T001453Z_performance-outcome-monthly/stdout.json`, run_id `65`.
  - Data-health stale remediation after API check: authorized `GET /api/data-health` returned `overall_status=healthy`; all affected jobs returned `health_status=ok`.
  - Data-health stale remediation UI smoke: `http://127.0.0.1:3001/data-health` rendered `정상`, `실패 파이프라인 0`, `수동 승인 대기`, and updated run ids.
  - Data-health stale remediation harness: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-health-stale-job-remediation`.
  - Data-health stale remediation diff check: `git diff --check`.
  - Market-price daily rollover artifact: `/private/tmp/stockanalysis-runtime/artifacts/20260519T010224Z_market-price-daily/stdout.json`.
  - Market-price daily rollover API check: authorized `GET /api/data-health` returned provider budget `configured`, `20` used, `780` remaining, latest market run `pipeline-run-89`, and market freshness `2026-05-18`.
  - Market-price daily rollover DB sample: expanded watchlist 20 symbols all have latest price date `2026-05-18`.
  - Market-price daily rollover frontend checks: `cd apps/web && npm run typecheck`, `cd apps/web && npm run build`.
  - Market-price daily rollover browser smoke: `/data-health` rendered `호출 예산 780 / 800`, `pipeline-run-89`, and `market.daily price bar observed · 2026-05-18`.
  - Market-price latest completed day policy focused tests: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price_free_backfill tests.test_data_operations_cli tests.test_data_operations_cadence -v`.
  - Market-price latest completed day zero-call smoke: `/private/tmp/stockanalysis-runtime/artifacts/20260519T011255Z_market-price-daily/stdout.json`, `freshness_policy=latest_completed_us_market_day`, `freshness_date=2026-05-18`, `provider_request_count=0`.
- Not run in this slice:
  - actual host `launchctl bootstrap`/`kickstart`.
  - split/dividend-adjusted real market-price ingest through Alpha Vantage premium endpoint.

## Exact Next Step

- exact next step: keep scheduler manual/pending until market non-trading dates are maintained outside the repo and alert destination is real, or move to real portfolio source integration.

## Risks

- Local data is mixed: FRED, SEC metadata, and AAPL market prices now include real-provider records; recommendation/thesis/performance data still depend partly on the fixture bootstrap path.
- Current ingest CLI still uses `STOCKANALYSIS_PSQL_COMMAND`; direct psycopg ingest is not implemented yet.
- 3000 is occupied by an unrelated `llm-wiki` Next server, so this cockpit uses 3001 until that process is stopped.
- Free `TIME_SERIES_DAILY` prices are not split/dividend adjusted; downstream quality checks must account for `price_adjustment_mode=unadjusted_fallback`.
- Twelve Data fixture normalization marks `price_adjustment_mode=split_adjusted_provider`, but actual adjusted-price behavior still needs a live smoke and provider-documentation drift check before performance attribution relies on it.
- Twelve Data runner is now freshness-aware only when `--skip-if-fresh` is explicitly enabled. The market-price daily scheduler default now includes it, but other ad hoc/manual commands can still omit it.
- Provider budget status can show `day_missing` after local date rollover until the next market-price run records a ledger entry for that date.
- Today's market-price rollover consumed 20 Twelve Data calls and solved the `day_missing` display. The follow-up zero-call smoke proved manual `--freshness-date` is no longer required for same-day rerun protection.
- Market holidays still require explicit non-trading dates in repo-outside env; no external exchange holiday calendar has been added.
- Expanded watchlist bars are provider-marked as `split_adjusted_provider`, but adjusted-price semantics still need provider drift checks before performance attribution relies on them.
- Local Alpha Vantage ledger now shows 24 calls remaining for 2026-05-17, but it is only a local accounting guard. The real account-side quota may be lower if the key is used outside this repo.
- `codex_oauth` depends on the local Codex CLI and ChatGPT login state, so it should stay in offline jobs with artifact capture/retry rather than FastAPI request paths.
