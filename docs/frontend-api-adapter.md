# Frontend API Adapter

이 문서는 frontend API contract examples를 반환하는 read-only Python adapter를 정의한다.

## Current Status

- `src/stockanalysis/frontend/api_adapter.py`를 추가했다.
- adapter는 `docs/api/frontend/contract-index.json`을 source of truth로 사용한다.
- exact API path를 linked example JSON으로 resolve한다.
- local HTTP fixture server는 `docs/frontend-fixture-server.md`와 `src/stockanalysis/frontend/fixture_server.py`에 추가됐다.
- `apps/web` scaffold는 fixture server를 통해 adapter output을 소비한다.
- live DB query adapter는 아직 없다.

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

## Verification

```bash
bash scripts/verify_frontend_api_adapter.sh
```

검증은 아래를 확인한다.

- `compileall`
- adapter unit tests
- frontend API contract verification
- CLI `list` smoke
- CLI `get --path /api/dashboard/today` smoke
- unknown path stable error
- root-level `app` scaffold가 없는 boundary

## Boundaries

- fixture adapter는 live DB freshness를 보장하지 않는다.
- exact path matching만 지원한다.
- query parameter normalization은 아직 없다.
- HTTP server는 `src/stockanalysis/frontend/fixture_server.py`에 있다.
- browser fetch 대상은 fixture server다.
- write command는 아직 없다.

## Next Steps

1. adapter output과 contract examples의 drift를 계속 검증한다.
2. `apps/web` detail routes를 fixture server payload로 확장한다.
3. live DB read adapter를 별도 boundary로 추가한다.
