# Recommendation investment memo v1

User authorized the proposed dependency and recommendation-detail work. This is the investor-facing task, separate from dependency PR #27.

## Goal

Reuse the existing recommendation executive brief and analyses to present the actual investment claim, supporting points, catalysts, risks, invalidation conditions, valuation assumptions, primary document links and recorded review date. Do not generate new investment claims or another audit subsystem.

## Scope

Existing Next.js recommendation detail, executive brief, position presentation and view model; a pure memo model; optional bounded linked-thesis read through the existing frontend API client; unit and real-route desktop/mobile browser tests using isolated fixtures. Exact linked thesis ID, symbol and instrument must match before any thesis text is displayed. A missing, mismatched or timed-out thesis must not remove the recommendation or independent research. Keep source labels and dates for thesis versus research rather than silently merging them.

Distinguish unknown positions from confirmed non-holdings, reference price from estimated value, expected evidence count zero from completeness, and ETF structure from company valuation. Missing risks/conditions/dates remain explicitly missing. Reuse existing deep-detail anchors and source-document/thesis routes. Source-blocked evidence takes priority. No raw network errors/credentials in UI.

## Acceptance

Company, ETF, source-blocked, unknown/missing data, missing/mismatched/stalled thesis cases; finite numeric/currency/date guards; per-source provenance; actual production route browser tests, scoped accessibility/overflow and screenshots; full frontend tests/build/typecheck; dependency audits remain gating. No write, order or financial-score behavior changes. Existing compatibility records keep their compact view.

## Boundaries

No backend/schema/benchmark/evaluation split, ranking/score/weight, allocation, portfolio, broker, production credentials, scheduler, deployment or live DB changes. An improved rendering is not validated investment performance. Review final diff and CI before merging to develop; main remains unchanged.
