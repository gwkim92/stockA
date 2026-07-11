# professional-workspace-cjk-copy-finalization-v1 Handoff

## Status

- completed: local implementation and verification are complete; the task is ready to commit.
- current status: completed locally and ready to commit; not deployed.
- branch: `codex/professional-workspace-cjk-copy-finalization-v1`.
- base commit: `817bd3b3`.
- deployment status: intentionally deferred until the subsequent frontend admin write-boundary task is complete.

## Outcome

- Korean prose now uses `word-break: keep-all` with an emergency long-token fallback, while short meaning units such as `아래 흐름`, `기업 자체`, `줄 수 있는`, `이 종목`, and `이 추천` remain intact and inherit the surrounding heading typography.
- Cycle ranking copy explicitly separates news evidence from deterministic cycle state.
- Professional-decision eligibility is fail-closed: only explicit review-ready statuses render as allowed.
- SPY/ETF source guardrails use concise company-model boundary wording and keep investment input, paper validation, and live-order status separate.
- Mobile execution-boundary rails collapse to one column so `읽기 전용, 주문 차단` is fully visible.
- Empty professional-flow data renders a labeled wait state, and price/broker cards fill their desktop and tablet grid rows instead of leaving unexplained gray regions.
- Summary recommendation tablet cards fill the final grid row.

## Root Cause

- Copy had been shortened to avoid Korean line breaks, which removed meaning without fixing narrow-container geometry.
- Shared title rules disabled emergency wrapping, while several nested `span` selectors overrode the surrounding heading typography.
- Explicit four-column status rails and incomplete tablet grid rows clipped safety copy or exposed empty background cells.
- Zero-step professional flows rendered an empty track with no explanation.
- Chromium full-page capture repeats content above 16,384px; the 21,127px expanded mobile view therefore requires exact segmented capture and lossless append.

## Verification Evidence

- `npm test`: 22 files / 50 tests passed.
- `npm run typecheck`: passed.
- `npm run build`: passed on Next.js 16.2.9.
- `npm run test:e2e`: 71 passed, 4 expected viewport-specific skips, 0 failed.
- `bash scripts/verify_frontend_api_contract.sh`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- `python3 -m awh verify --repo . --task professional-workspace-cjk-copy-finalization-v1`: passed.
- `git diff --check`: passed.
- Fresh final8 browser evidence contains 21 primary screenshots, 10 layout/safety crops, 3 exact mobile segments, and 5 phrase crops at 375/768/1280px.
- Browser metrics: no console errors, error states, or horizontal overflow; all protected phrases are one line, within the viewport, and match parent font size/weight/line height; all execution badges are contained.
- Independent design/functional review: `PASS`, high confidence, 39/39 images.
- Independent Korean/CJK review: `PASS`, high confidence, 39/39 images.
- The 21,127px expanded mobile composite is a lossless append of the exact 0–8,000, 8,000–16,000, and 16,000–21,127px captures; reviewers confirmed continuity and no repeated header.

## Exact Next Step

- exact next step: commit only the intended source, tests, plan, contract, handoff, and review; then start `admin-server-action-auth-boundary-v1` on a fresh task branch.
- Keep `.omo/`, `apps/test-results/`, `apps/web/test-results/`, `dogfood-output/`, and `output/playwright/` out of staging.

## Guardrails

- Recommendation weights remain unchanged.
- Benchmark definitions and portfolio positions remain unchanged.
- Automatic weight change, automatic orders, and broker submit remain disabled.
- Order boundary remains `read_only_no_order`.

## Residual Risks

- Final8 browser evidence uses the local fixture-backed production build; EC2 live state and deployment are not verified in this task.
- The full-page visual capture stabilizes sticky-only regions as static to avoid screenshot contamination; ordinary E2E exercises the unmodified production CSS.
- Manual weight review remains outside this task and still requires separate approval after current outcome/portfolio-feedback gates are re-read.
