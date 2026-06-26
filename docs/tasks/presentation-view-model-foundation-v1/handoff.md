# presentation-view-model-foundation-v1 Handoff

## Status

- implemented locally on `feature/professional-investment-ux-normalization-v1`.

## Target View Model Shape

- `title`
- `summary`
- `statusLabel`
- `statusTone`
- `investmentImpact`
- `nextAction`
- `sourceLimitReason`
- `metrics`

## Implemented

- Added typed presentation modules under `apps/web/src/lib/presentation/`:
  `view-model.ts`, `recommendation.ts`, `stock.ts`, `portfolio.ts`, `paper.ts`, `operations.ts`.
- Wired the presentation layer into recommendation detail, stock detail, portfolio coverage, paper trading, and data-health overview copy.
- Added `apps/web/src/lib/presentation/research-view-models.test.ts` to lock core investor-facing copy mappings.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm test` (`14` files, `36` tests)
- `cd apps/web && npm run build`
- `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e` (`51` passed)

## Remaining

- Route files still contain legacy raw DTO interpretation in deeper sections. Continue moving visible copy into presentation view models as each large page is split.
