# Implementation Plan

- Add live adapter path parsing for `/api/cycles`.
- Add a SQL renderer that returns contract-shaped cycle list state from existing canonical tables.
- Add DTO builders for cycle state item normalization.
- Extend `FakeLiveExecutor` with cycle list payloads.
- Add contract-shape tests for cycle list and schema-column guard assertions.
- Update frontend adapter/contract/roadmap docs.
- Run live adapter verification, roadmap verification, AWH, placeholder scan, and diff check.
