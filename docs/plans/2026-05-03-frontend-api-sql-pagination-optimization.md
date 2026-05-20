# FastAPI Frontend API SQL Pagination Optimization Plan

Date: 2026-05-03

## Summary

`frontend-api-pagination-conventions`에서 고정한 `limit`/opaque `cursor` contract를 유지하되, live read path는 전체 JSON 배열을 만든 뒤 Python에서 자르지 않는다. collection SQL/report boundary에 `limit + 1`과 cursor offset을 전달하고, 초과 row 존재 여부로 `pagination.has_more`와 `next_cursor`를 계산한다.

## Scope

- 대상 endpoint:
  - `/api/cycles?asOfDate=...`
  - `/api/events?asOfDate=...`
  - `/api/performance/{portfolio}/outcomes?measurementEndDate=...`
  - `/api/remediation-tickets`
  - `/api/portfolio/{portfolio}/coverage?asOfDate=...`
- 유지:
  - 기존 DTO shape
  - 기존 opaque v1 offset cursor wire format
  - FastAPI/fixture pagination error contract
- 제외:
  - DB schema/index migration
  - keyset cursor v2
  - auth/RBAC/write APIs
  - frontend table implementation

## Implementation Steps

1. Add `apply_frontend_sql_pagination()` and `frontend_sql_page_window()` helper tests.
2. Call `frontend_sql_page_window()` from live list endpoint builders.
3. Add bounded `limit/offset` clauses to cycle/event/performance list SQL while preserving full summaries.
4. Add remediation report `offset`.
5. Add paged portfolio coverage report SQL that computes summary on all rows and `positions` on the page window.
6. Add verification script and update project docs/handoff.

## Design Notes

- This is SQL-level bounded offset pagination, not true keyset pagination.
- The existing cursor stays opaque so a future v2 keyset payload can be introduced without exposing internal SQL order details.
- `limit + 1` is used only for `has_more`; response payload trims back to the requested `limit`.
