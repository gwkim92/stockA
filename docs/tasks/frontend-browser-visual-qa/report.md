# Frontend Browser Visual QA Report

| Field | Value |
|-------|-------|
| Date | 2026-05-01 |
| App URL | `http://127.0.0.1:3006` |
| Fixture API | `http://127.0.0.1:8766` |
| Scope | Expanded fixture-backed frontend routes: dashboard, events, theme detail, performance, portfolio coverage |
| Browser Tool | `agent-browser` with production Next build |

## Route Coverage

| Route | Viewport | Evidence | Console/Errors |
|-------|----------|----------|----------------|
| `/` | 1440x1000 | `output/playwright/frontend-browser-visual-qa/screenshots/prod-desktop-dashboard.png` | production console clean |
| `/events` | 1440x1000 | `output/playwright/frontend-browser-visual-qa/screenshots/prod-desktop-events.png` | production console clean |
| `/themes/ANNUAL_REPORTING` | 1440x1000 | `output/playwright/frontend-browser-visual-qa/screenshots/prod-desktop-theme.png` | production console clean |
| `/performance` | 1440x1000 | `output/playwright/frontend-browser-visual-qa/screenshots/prod-desktop-performance-final.png` | production console clean |
| `/performance` | 390x844 | `output/playwright/frontend-browser-visual-qa/screenshots/prod-mobile-performance-final3.png` | production console clean; `clientWidth=390`, `scrollWidth=390` |
| `/portfolio/coverage` | 1440x1000 | `output/playwright/frontend-browser-visual-qa/screenshots/prod-desktop-coverage.png` | production console clean |

## Findings

### ISSUE-001: Mobile performance route created horizontal overflow

| Field | Value |
|-------|-------|
| Severity | medium |
| Category | visual / responsive |
| URL | `http://127.0.0.1:3002/performance` |
| Status | fixed |
| Repro Video | N/A |

**Description**

At 390px viewport width, the performance page extended beyond the viewport. The top navigation and several `bento-card` list items caused horizontal scroll and squeezed the outcome row into a narrow column. This made mobile review harder and could hide content off-screen.

**Evidence**

- Before fix annotated screenshot: `output/playwright/frontend-browser-visual-qa/screenshots/prod-mobile-performance.png`
- After nav containment fix, card content still overflowed: `clientWidth=390`, `scrollWidth=431`
- Final after grid/list fixes: `clientWidth=390`, `scrollWidth=390`
- Final screenshot: `output/playwright/frontend-browser-visual-qa/screenshots/prod-mobile-performance-final3.png`

**Fix**

- Added `min-width: 0`, `max-width: 100%`, and `overflow-x: auto` to the top navigation container.
- Added `min-width: 0` and wrapping behavior to bento cards/list items.
- Added mobile list item stacking so narrow screens do not compress outcome metadata.

## Notes

- The first dev-server browser pass showed Next HMR WebSocket console noise. Production build/start was used for final QA, and production console/errors were clean.
- This QA used fixture data only. It does not prove live DB freshness or production deployment behavior.
