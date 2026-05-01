# Implementation Plan

- Extend `src/stockanalysis/frontend/fixture_server.py` with `source` mode.
- Keep `fixture` as the default source so existing frontend smoke remains stable.
- Pass source mode into `resolve_frontend_response`.
- Map `FrontendLiveReadUnavailable` to HTTP 503 and unsupported live path to HTTP 501.
- Add `source_mode` to `/__health`, `/__endpoints`, startup JSON, and `X-Stockanalysis-Source`.
- Add fixture server tests for default fixture, auto fallback, and live missing-config error.
- Update `scripts/verify_frontend_fixture_server.sh` with auto/live runtime smoke.
- Update frontend runtime docs and task handoff/review.
- Run fixture server, live adapter, detail route, AWH, placeholder, and diff checks.
