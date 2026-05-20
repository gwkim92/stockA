# Frontend API SQL Pagination Optimization

Date: 2026-05-03

## Decision

Frontend read-only live list endpoints now push the existing pagination contract into the SQL/report boundary.

- Wire format remains `limit` plus opaque v1 offset cursor.
- Live readers request `limit + 1` rows and the current cursor offset.
- Response boundary trims the extra row and keeps the existing top-level `pagination` metadata.
- Fixture mode keeps response-boundary pagination because fixture JSON is already bounded local test data.

## Implemented Endpoints

- `/api/cycles?asOfDate=...`
- `/api/events?asOfDate=...`
- `/api/performance/{portfolio}/outcomes?measurementEndDate=...`
- `/api/remediation-tickets`
- `/api/portfolio/{portfolio}/coverage?asOfDate=...`

## Data Boundary

`frontend_sql_page_window()` parses the existing request path and returns `(limit + 1, offset)`. Live adapter builders pass that window into SQL/report loaders.

`apply_frontend_sql_pagination()` expects that the SQL/report payload already contains at most `limit + 1` collection rows. It trims the collection back to `limit`, computes `has_more`, and emits `next_cursor` as the next opaque offset cursor.

## Summary Semantics

- Event and performance summaries remain computed from the full filtered set.
- Remediation ticket counts now come from `filtered_tickets`; only `tickets` are paged.
- Portfolio coverage summary remains computed from all matching positions; only `positions` are paged.

## Guardrails

- No DB schema, benchmark, scoring, or evaluation split changed.
- No frontend UI table work was included.
- No auth/RBAC/write endpoint work was included.
- No secrets or deployment config were changed.

## Remaining Risk

This is SQL-level bounded offset pagination, not true keyset pagination. It prevents full JSON payload construction for normal API pages, but very deep pages can still pay offset scan cost. If query plans show that cost matters, the next optimization should introduce a v2 keyset cursor with per-endpoint stable sort keys and matching composite indexes.
