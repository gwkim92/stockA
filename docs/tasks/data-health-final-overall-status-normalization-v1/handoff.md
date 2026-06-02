# data-health-final-overall-status-normalization-v1 Handoff

## Status

- status: in_progress
- in progress: final data-health status normalization is implemented locally and needs commit, EC2 deploy, and smoke verification.
- current status: code change is implemented locally and awaiting final verification, commit, EC2 deploy, and smoke.

## Context

- Local `127.0.0.1:13000` tunnel was down because no SSH tunnel process was listening on local port `13000`.
- EC2 FastAPI and Next.js services were active.
- Recreated SSH tunnel to EC2 Next.js: local `13000` -> EC2 `127.0.0.1:3000`.
- `/` and `/data-health` returned HTTP 200 through the tunnel.
- EC2 data-health then showed two actionable gates:
  - `active_recommendation_price_freshness_attention`
  - `professional_source_gap_attention`

## Operational Remediation

- Created repo-outside watchlist `/opt/stockanalysis/runtime/active-recommendation-price-backfill-watchlist-20260602.csv` with `ALAB`, `ARM`, `DIS`, `ELF`.
- Ran `market-price-free-backfill-run` with Twelve Data, `freshness-date=2026-06-01`.
- Result: 4/4 succeeded, 400 bars inserted, latest trade date `2026-06-01`, provider requests used `4`.
- Created repo-outside ADSK-only SEC ticker JSON `/opt/stockanalysis/runtime/company-tickers-ADSK-20260602.json`.
- Dry-run confirmed professional coverage target was ADSK only; `EROK` and `SPY` stayed unmatched.
- Ran `professional-coverage-expansion-run --research-provider codex_oauth --execute`.
- Result: `run_id=2833`, ADSK companyfacts `fact_count=1727`, downstream financial/peer/forecast/segment/SOTP/valuation/industry/equity research reports completed, `inserted_artifact_count=1`, `recommendation_scoring_mutated=false`, `broker_order_submit_enabled=false`.

## Code Change

- Added final overall status normalization so `/api/data-health.overall_status` follows final post-policy `open_gates`.
- Added unit coverage for fallback `attention_required` with no final open gates returning `healthy`.

## Remaining Verification

- exact next step: run local verification, commit, deploy to EC2, and verify `/api/data-health` reports `overall_status=healthy` with `open_gates=[]`.
- Run local unit/compile/typecheck.
- Deploy commit to EC2.
- Verify `/api/data-health` reports `overall_status=healthy`, `open_gates=[]`.
- Verify `http://127.0.0.1:13000/` and `/data-health` return HTTP 200.
