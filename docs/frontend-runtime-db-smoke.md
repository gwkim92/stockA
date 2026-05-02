# Frontend Runtime DB Smoke

이 문서는 read-only frontend HTTP runtime이 fixture JSON이 아니라 실제 Postgres state를 live DTO로 반환하는지 검증하는 smoke를 설명한다.

## Purpose

`frontend-runtime-db-smoke`는 아래 경계를 증명한다.

- migrations와 seeds가 적용된 Postgres에서 canonical state를 읽는다.
- deterministic fixture pipeline으로 생성한 실제 DB state를 사용한다.
- HTTP runtime은 `source=live`로 실행된다.
- production runtime profile, explicit CORS, read-token auth가 함께 적용된다.
- `/__health`는 public이고 `/api/...`는 bearer token 없이는 거부된다.
- write endpoint, browser DB credential, broker/order flow는 여전히 없다.

## Command

```bash
bash scripts/verify_frontend_runtime_db_smoke.sh
```

이 스크립트는 Docker Postgres container를 disposable로 시작하고 종료 시 제거한다.

## Checked HTTP Paths

- `/__health`
- `/api/dashboard/today`
- `/api/data-health`
- `/api/cycles?asOfDate=2024-11-01`
- `/api/events?asOfDate=2024-11-01`
- `/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01`
- `/api/remediation-tickets?status=open`
- `/api/recommendations/AAPL-2024-11-01`
- `/api/theses/AAPL-bootstrap-v1`
- `/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02`
- `/api/source-documents/0000320193-24-000123`

## Boundaries

- This is a smoke, not a production API server.
- The runtime still shells out through `STOCKANALYSIS_PSQL_COMMAND`.
- Connection pooling, request id, OpenAPI route index, and server framework decision are next.
- `read-token` remains a deployment seam, not full user identity or RBAC.
- No schema, benchmark, scoring, or evaluation split is changed by this smoke.
