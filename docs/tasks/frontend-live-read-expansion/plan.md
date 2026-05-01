# Implementation Plan

- Add live adapter SQL renderers for dashboard state and data health state.
- Add parser functions that normalize SQL JSON payloads into frontend DTOs.
- Route `/api/dashboard/today` and `/api/data-health` in `resolve_live_frontend_response`.
- Update `is_live_supported_path`.
- Extend `FakeLiveExecutor` with dashboard/data-health payloads.
- Add tests for dashboard/data-health contract shape.
- Run live adapter verification and AWH.
- Update docs and task handoff/review.
