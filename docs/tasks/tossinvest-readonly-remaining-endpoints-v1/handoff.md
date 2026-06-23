# TossInvest Readonly Remaining Endpoints V1 Handoff

## Status

- completed locally: remaining TossInvest read-only endpoint builders, bounded summaries, and frontend read-model exposure are implemented and verified locally.

## Current Decisions

- Remaining Toss endpoints are read-only only.
- New live calls should be folded into the existing manual `tossinvest-readonly-sync-run` before any scheduler activation.
- Full raw orderbook/trades/order history archival is not added in this task; bounded summaries are surfaced through existing read models.
- Order history detail is fetched only for a bounded subset and report output stores status/symbol/side counts, not raw order ids.
- Optional market-data endpoint failures are summarized per symbol and do not fail the core holdings/FX sync.

## Guardrails

- Do not log Toss client secret, access token, account sequence/account number, Authorization header, or full raw order identifiers beyond safe counts/status summaries.
- Do not call Toss order submit, modify, or cancel endpoints.
- Do not change recommendation weights, benchmark definitions, portfolio order flows, or broker submit boundary.

## Verification Notes

- passed: `bash scripts/verify_tossinvest_remaining_readonly_endpoints.sh`
- passed: `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- passed: `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests` (`1255` tests)

## Residual Risk

- Live Toss rate-limit behavior for these additional endpoint groups needs EC2 smoke after deploy.
- Production scheduler and market-data default provider remain unchanged.

## Exact Next Step

- exact next step: Deploy to EC2, run `tossinvest-readonly-sync-run --execute`, verify `/api/data-health` and `/api/trading/readiness` expose the new read-only summaries, and confirm no order submission path is enabled.
