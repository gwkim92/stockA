# Recommendation Quality Audit v1 — verification checkpoints

Base develop: db933728934078f8de099685883fbc9a5bd3cdd7.

## Early failures corrected without weakening checks

Initial feature CI on aea31ad4599e4e08b71a746497794c3e89fe0fb6 failed one new unit assertion because binary floating-point produced 0.019999999999999997 for the arithmetic mean of +0.06 and -0.02. The production calculation was unchanged. The test now uses a tight numerical tolerance rather than exact decimal identity.

Head 92656f66cf1869c8ac9deeae467f5c7c82616622 / Web Product Quality 34091534954 then passed dependency audits, 123 Python display/adapter tests, 512 frontend tests across 39 files, production build/typecheck, all 168 notebook browser tests and all 64 investor browser tests. Its holdings/outcomes suite passed 34/36. Both new recommendation-quality scenarios passed on desktop and mobile, including axe and width assertions. The two failures were an existing product-level first-record visibility check: inserting the full audit before actual recommendation outcomes moved the first record to y=2377 on desktop and y=3730 on mobile, violating the existing <900/<780 thresholds. Later browser suites were skipped in that failed run and are not counted as passes.

The assertion and thresholds remain unchanged. The detailed audit is moved below OutcomeExplorer so users see actual recommendation outcomes before secondary aggregate diagnostics. Review metrics remain above both. This is a product-order correction, not test accommodation; the audit's content and dedicated accessibility/layout tests remain intact. An unused model import was also removed with no behavior change.

## Required final evidence

The final branch must pass the unchanged full Web Product Quality workflow: Python display/adapter checks, all frontend units, production build/typecheck, audits, notebook, investor, holdings/outcomes, readers, company/evidence and news/theme browsers. Final screenshots must be inspected for both the early recommendation records and the audit panel on desktop/mobile. Exact observed counts, artifact identity/hash, merge SHA and post-merge result belong in the PR after observation.

No backend/SQL/schema/migrations/seeds, recommendation scoring/weights, benchmark/evaluation golden data, portfolio/order/broker writes, dependencies/lockfile, workflow, secrets/AWS, scheduler, main or deployment changes are part of this task.
