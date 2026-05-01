# Frontend Fixture Server

이 문서는 frontend API contract examples를 local HTTP로 제공하는 read-only fixture server를 정의한다.

## Current Status

- `src/stockanalysis/frontend/fixture_server.py`를 추가했다.
- server는 `src/stockanalysis/frontend/api_adapter.py`를 감싸며, source of truth는 `docs/api/frontend/contract-index.json`이다.
- Python standard library `http.server` 기반이라 별도 web framework dependency를 추가하지 않는다.
- `apps/web` scaffold는 fixture server를 browser fetch source로 사용한다.
- live DB adapter, production API server, auth/RBAC는 아직 없다.

## Start Server

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port 8765
```

Console script entrypoint:

```bash
stockanalysis-frontend-fixture-server --host 127.0.0.1 --port 8765
```

The server prints a JSON startup payload containing `base_url` and `health`.

## Endpoints

Health:

```bash
curl http://127.0.0.1:8765/__health
```

Endpoint index:

```bash
curl http://127.0.0.1:8765/__endpoints
```

Fixture examples:

```bash
curl http://127.0.0.1:8765/api/dashboard/today
curl 'http://127.0.0.1:8765/api/remediation-tickets?status=open'
```

## Error Shape

Unknown path returns HTTP 404:

```json
{
  "error": {
    "code": "FrontendApiPathNotFound",
    "message": "Unknown frontend API path: /api/not-found",
    "details": {
      "method": "GET",
      "path": "/api/not-found"
    }
  }
}
```

Unsupported write methods return HTTP 405:

```json
{
  "error": {
    "code": "MethodNotAllowed",
    "message": "Method POST is not allowed for the frontend fixture server.",
    "details": {
      "allowed_methods": ["GET", "HEAD", "OPTIONS"],
      "method": "POST"
    }
  }
}
```

## Verification

```bash
bash scripts/verify_frontend_fixture_server.sh
```

검증은 아래를 확인한다.

- `compileall`
- fixture server unit tests
- frontend API adapter verification
- CLI help smoke
- in-process HTTP runtime smoke
- known path response
- query-string path response
- unknown path 404
- write method 405
- root-level `app` scaffold가 없는 boundary

## Boundaries

- fixture server는 local development와 frontend smoke용이다.
- fixture server는 live DB freshness를 보장하지 않는다.
- exact path matching만 지원한다.
- query parameter normalization은 아직 없다.
- write endpoint는 구현하지 않는다.
- production deployment, auth, RBAC는 아직 없다.

## Next Steps

1. `apps/web` detail routes를 fixture server payload로 확장한다.
2. live DB read adapter를 별도 boundary로 추가한다.
3. auth/RBAC와 audit trail이 준비된 뒤에만 remediation ticket status write endpoint를 추가한다.
