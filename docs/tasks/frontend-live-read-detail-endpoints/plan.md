# Implementation Plan

- Add live adapter path parsing for recommendation, thesis, AI evidence, and source document detail endpoints.
- Add SQL renderers that return denormalized JSON objects from existing canonical tables.
- Add DTO builders that normalize IDs, timestamps, numbers, links, evidence arrays, and access policy.
- Extend `FakeLiveExecutor` with detail endpoint payloads.
- Add contract-shape tests for all four endpoints.
- Update frontend adapter/contract/roadmap docs.
- Run live adapter verification, AWH, placeholder scan, and diff check.
