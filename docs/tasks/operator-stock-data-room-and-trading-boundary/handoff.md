# Session Handoff

## Active Task

- 이름: operator-stock-data-room-and-trading-boundary
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract and handoff created.
  - `/api/stocks` and `/api/stocks/{symbol}` read-only DTOs added.
  - `/stocks` and `/stocks/[symbol]` operator pages added.
  - live FastAPI and Next local route smokes passed.
  - Playwright snapshots confirmed Korean operator wording, stock rows, and AAPL chart/detail sections.
- 진행 중:
  - none.
- 막힌 점:
  - none for this slice.

## Completed Details

- Added read-only frontend API DTOs for `/api/stocks` and `/api/stocks/{symbol}`.
- Added live Postgres SQL read models over `ref.instrument`, `market.daily_price_bar`, `signal.recommendation`, `portfolio.position_snapshot`, and linked `event.*` evidence.
- Added fixture contract examples and registered the endpoints in `docs/api/frontend/contract-index.json`.
- Added Next.js pages:
  - `/stocks`: collected stock list with latest price, price coverage, recommendation state, and position state.
  - `/stocks/[symbol]`: price chart, latest price, data coverage, recommendation, position, and recent linked events.
- Simplified top navigation wording:
  - `데이터 수집`, `종목`, `해야 할 일`, `보유 검토`, `AI 근거`.
- Updated project roadmap contract count from 12 to 14 DTOs.
- Updated verification plan wording from twelve to fourteen frontend example JSON files.

## Exact Next Step

- exact next step: rerun full Python regression and AWH verify after the `tests/test_frontend_fixture_server.py` endpoint count update; then continue with a new backend task for paper trading ledger and recommendation-quality evaluation, not real broker order placement.

## Live Evidence

- FastAPI local live server is running on `http://127.0.0.1:8787`.
- Next local frontend is reachable on `http://127.0.0.1:3001`.
- `GET /api/stocks?limit=1` returned live DB data:
  - `stock_count=27`
  - `latest_price_date=2026-05-18`
  - first row `AAPL`, latest close `300.23001`, price coverage `104` bars.
- `GET /stocks` returned HTTP 200.
- `GET /stocks/AAPL` returned HTTP 200.
- Playwright snapshots confirmed the pages show Korean operator wording, stock rows, and AAPL chart/detail sections.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter`: passed.
- `python3 -m json.tool docs/api/frontend/contract-index.json`: passed.
- `python3 -m json.tool docs/api/frontend/examples/stock-list.json`: passed.
- `python3 -m json.tool docs/api/frontend/examples/stock-detail.json`: passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`: passed, 483 tests.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task operator-stock-data-room-and-trading-boundary`: passed.

## Remaining Work

- Full Python regression initially found one stale endpoint-count assertion in `tests/test_frontend_fixture_server.py`; it was patched from `12` to `14` and the rerun passed.
- Real trading remains blocked until broker selection, account permission boundary, paper-trade validation, order limits, kill switch, audit log, and explicit approval exist.
- Host scheduler activation remains blocked by repository rule until exact command, repo-outside env, dry-run evidence, and explicit user approval are present.
- Recommendation quality and AI RAG/ontology should be the next backend slices after the operator can inspect collected stock data.
- Current DB data exposes one important data-quality issue: AAPL is marked as `exclude` but the paper portfolio snapshot still holds `100%` weight. This is visible now and should become a remediation rule.
