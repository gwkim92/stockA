# Frontend API Adapter

이 문서는 frontend API contract examples와 일부 live Postgres read model을 반환하는 read-only Python adapter를 정의한다.

## Current Status

- `src/stockanalysis/frontend/api_adapter.py`를 추가했다.
- adapter는 `docs/api/frontend/contract-index.json`을 source of truth로 사용한다.
- exact API path를 linked example JSON으로 resolve한다.
- local HTTP fixture server는 `docs/frontend-fixture-server.md`와 `src/stockanalysis/frontend/fixture_server.py`에 추가됐다.
- `apps/web` scaffold는 fixture server를 통해 adapter output을 소비한다.
- live DB read adapter pilot은 `src/stockanalysis/frontend/live_adapter.py`에 추가됐다.
- live source는 현재 dashboard, data health, cycle list, events, theme detail, performance outcomes, recommendation detail, thesis detail, AI evidence detail, source document detail, remediation tickets, portfolio coverage endpoint를 지원한다.

## CLI

List endpoints:

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter list
```

Get a fixture response:

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get \
  --path "/api/dashboard/today"
```

Get a live DB response:

```bash
STOCKANALYSIS_PSQL_COMMAND='psql postgresql://...' \
PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get \
  --source live \
  --path "/api/dashboard/today"
```

Use live when configured, otherwise fixture fallback:

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get \
  --source auto \
  --path "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01"
```

Unknown path returns non-zero exit code and stable error JSON:

```json
{
  "error": {
    "code": "FrontendApiPathNotFound",
    "message": "Unknown frontend API path: /api/not-found",
    "details": {}
  }
}
```

## Python API

```python
from stockanalysis.frontend.api_adapter import resolve_frontend_response

payload = resolve_frontend_response("/api/dashboard/today")
```

Live read pilot:

```python
from stockanalysis.frontend.live_adapter import resolve_live_frontend_response

payload = resolve_live_frontend_response("/api/remediation-tickets?status=open")
```

`resolve_frontend_response(..., source="auto")` only attempts live reads when the path is supported and `STOCKANALYSIS_PSQL_COMMAND` is configured.

## Verification

```bash
bash scripts/verify_frontend_api_adapter.sh
bash scripts/verify_frontend_live_read_adapter.sh
```

검증은 아래를 확인한다.

- `compileall`
- adapter unit tests
- frontend API contract verification
- CLI `list` smoke
- CLI `get --path /api/dashboard/today` smoke
- unknown path stable error
- live adapter unit tests
- live source missing-config stable error
- auto source fixture fallback when DB config is absent
- root-level `app` scaffold가 없는 boundary

## Boundaries

- fixture source는 live DB freshness를 보장하지 않는다.
- live source는 `STOCKANALYSIS_PSQL_COMMAND`가 필요하다.
- live source 지원 endpoint는 현재 `GET /api/dashboard/today`, `GET /api/data-health`, `GET /api/cycles?asOfDate=...`, `GET /api/events?asOfDate=...`, `GET /api/themes/:themeKey?asOfDate=...`, `GET /api/performance/:portfolio/outcomes?measurementEndDate=...`, `GET /api/recommendations/:id`, `GET /api/theses/:id`, `GET /api/ai-evidence/:id`, `GET /api/source-documents/:id`, `GET /api/remediation-tickets?status=open`, `GET /api/portfolio/:portfolioName/coverage?asOfDate=...`다.
- exact path matching만 지원한다.
- query parameter normalization은 live pilot에서 필요한 최소 범위만 지원한다.
- HTTP local runtime은 `src/stockanalysis/frontend/fixture_server.py`에 있고 `--source fixture|live|auto`를 지원한다.
- browser fetch 대상은 기본적으로 fixture server이며, local run에서는 `--source auto`로 live-supported endpoint만 DB를 읽게 할 수 있다.
- runtime boundary policy는 `docs/frontend-api-runtime-boundary.md`에 있고 local/prod profile, CORS, read-token auth seam을 정의한다.
- write command는 아직 없다.
- production API server framework, connection pooling, full auth/RBAC는 아직 없다.

## Next Steps

1. actual DB-backed HTTP live success smoke를 추가한다.
2. production API server framework와 connection pooling을 설계한다.
3. auth/RBAC와 audit trail이 준비된 뒤에만 write endpoint를 추가한다.
