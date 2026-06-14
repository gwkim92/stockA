# correlation-risk-visibility-v1 Handoff

## Status

- completed locally; pending EC2 deploy/smoke.

## Current Status

- 상태: local verification passed.
- 기준일: 2026-06-14
- 완료:
  - task contract created.
  - correlation runner filters self/proxy duplicate pairs such as `instrument:QQQ` versus `indicator:QQQ`.
  - correlation runner clears target date/lookback rows before reinsert so stale duplicate rows are removed on rerun.
  - stock detail live API returns `market_correlations`.
  - recommendation detail live API returns `market_correlations`.
  - `/stocks/[symbol]` shows market co-movement risk after price data.
  - `/recommendations/[recommendationId]` shows recommendation-level market co-movement risk.
- 막힌 점:
  - none.

## Implemented

- `src/stockanalysis/operations/correlation_analysis.py`
  - added self/proxy duplicate filters.
  - changed rerun behavior to delete same date/lookback snapshots before insert in a single PostgreSQL statement.
- `src/stockanalysis/frontend/live_adapter.py`
  - added latest correlation lookup CTEs for stock and recommendation detail state.
  - added Korean non-causal summaries for co-movement rows.
- `apps/web`
  - added shared `AssetCorrelation` type usage.
  - added correlation counts/cards/sections to stock and recommendation detail pages.
- `tests`
  - added unit and frontend contract coverage for correlation deduplication and API payloads.

## Verification

- Passed:
  - `PYTHONPATH=src python3 -m unittest tests.test_correlation_analysis tests.test_frontend_live_adapter`
  - `PYTHONPATH=src python3 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task correlation-risk-visibility-v1`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- Note:
  - `PYTHONPATH=src python3 -m unittest discover -s tests` with default Homebrew Python 3.14 fails outside this task because the local Python 3.14 `pyexpat` is broken and FastAPI is not installed in that interpreter. The repo runtime should use Python 3.13/venv.

## Exact Next Step

- exact next step: commit/push to `develop`, pull on EC2, rerun `correlation-analysis-run --as-of-date 2026-06-14 --execute`, then smoke `/market-map`, `/stocks/QQQ`, and a recommendation detail route.

## Notes

- Correlation remains co-movement analysis only. It must not be described as causal evidence.
- Recommendation scoring weights and broker/order boundaries must remain unchanged.
