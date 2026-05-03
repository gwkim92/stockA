# Frontend API Pagination Conventions

이 문서는 read-only frontend API list endpoint의 pagination contract를 정의한다.

## Current Status

- helper: `src/stockanalysis/frontend/pagination.py`
- verification: `scripts/verify_frontend_api_pagination_conventions.sh`
- default limit: `50`
- max limit: `100`
- cursor format: opaque v1 cursor

## Response Shape

Collection responses keep their existing `data` shape and add top-level `pagination`.

```json
{
  "contract_version": "frontend-api-v0.1",
  "generated_at": "2026-05-01T00:00:00Z",
  "data": {},
  "pagination": {
    "limit": 50,
    "cursor": null,
    "next_cursor": null,
    "has_more": false,
    "item_count": 0
  },
  "links": {}
}
```

Rules:

- `limit` is optional and defaults to `50`.
- `limit` must be an integer from `1` through `100`.
- `cursor` is optional and opaque to clients.
- Clients must pass `next_cursor` as the next request's `cursor`.
- Clients must not parse cursor contents.
- Page-number pagination is not supported.
- Invalid pagination returns `FrontendPaginationInvalid`.

## Collection Endpoints

Initial collection endpoints:

- `/api/remediation-tickets?status=open`: collection key `tickets`
- `/api/cycles?asOfDate=...`: collection key `cycle_states`
- `/api/events?asOfDate=...`: collection key `events`
- `/api/portfolio/:portfolio/coverage?asOfDate=...`: collection key `positions`
- `/api/performance/:portfolio/outcomes?measurementEndDate=...`: collection key `outcomes`

Detail endpoints reject `limit` or `cursor`.

## Boundary

This slice applies response-boundary pagination after DTO construction. It establishes API contract and runtime validation before SQL-level cursor seek optimization.

Implications:

- Existing `data` fields remain backward compatible.
- Large production lists still need SQL-level pagination before broad scale.
- Cursor format can be versioned later if SQL-level cursors replace offset cursors.

## Verification

```bash
bash scripts/verify_frontend_api_pagination_conventions.sh
```

The verification checks helper behavior, fixture adapter behavior, live adapter behavior, FastAPI error mapping, example DTO metadata, and TypeScript response type compatibility.
