# Equity context cutoff v1

Continue stockA after PR #37. Base develop@d7ad05cbd7599d5cdb5fb8782b84b4cdca945448.

## Reproduced source findings

The equity context query does not limit thesis.created_at, prefers today's active status, and includes events at the next midnight using a session-timezone-dependent comparison. A later thesis can therefore enter an earlier requested context. Fix these concrete selection issues without claiming a complete point-in-time dataset.

## Scope

Use an explicit UTC exclusive end-of-day bound for thesis creation and event occurrence. A future linked thesis must not bypass the bound. Among eligible theses retain explicit recommendation linkage, then choose by creation time/ID rather than current active status. Expose original thesis creation/closure timestamps and a query temporal-policy marker. Teach the existing equity prompt that selected current stored text is not an immutable historical version. Preserve the provider/hash/input inventory alignment from PR #37. Add actual PostgreSQL query tests, not only SQL-string assertions, and retain the existing offline prompt regressions.

## Verification

Execute the generated production SELECT against a disposable, synthetic PostgreSQL service in CI with no host port, no production credentials/endpoint and no external data. Test UTC/Seoul/New York session zones, DST dates, exact midnight/microsecond boundaries, future recommendation links, same-time IDs, current-status changes, missing and cross-instrument theses, end-to-end prompt selection and source inventory. Compare baseline and changed SQL against identical data to demonstrate the defects. Keep test-only writes in a rollback transaction; this database is an isolated test fixture, not a replacement for stockA's existing runtime.

## Boundaries and limits

No production DB access or mutation, migration/seed changes, dependency/lockfile, financial scoring/weights, benchmark/evaluation split, portfolio/order/broker, main, account/secrets/AWS, scheduler or deployment configuration changes. No model calls. The existing thesis schema lacks immutable body revisions; earlier-created bodies can be edited later. Events can be ingested/translated later, and other snapshot/association fields are mutable. This repair restricts creation/event time, not complete knowledge-at-the-time provenance or a backtest certification. Record those limitations in prompts and handoff. Mixed-symbol batch failure isolation remains a separate task.