# Implementation Plan

- Add live adapter path parsing for events, theme detail, and performance outcomes.
- Add SQL renderers that return denormalized JSON objects from canonical Postgres tables.
- Add DTO builders that normalize IDs, timestamps, ratios, links, and quality gates.
- Extend `FakeLiveExecutor` with event/theme/performance payloads.
- Add contract-shape tests for all three endpoints.
- Update frontend adapter/contract/roadmap docs.
- Run live adapter verification, AWH, placeholder scan, and diff check.
