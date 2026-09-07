# Research payload contract v1

Continue user-requested stockA implementation from develop@45a33cfd281ce21c31246a039bff93f0924770f7 (PR #44). Post-merge run 34078636820 is confirmed successful. The unresolved manual screenshot inspection remains unresolved: container and Python each returned ClientError in this session. Do not keep retrying or claim pixels were inspected.

## Product goal

Verify that the actual Python stock-detail adapter's saved equity research reaches the TypeScript company and review screens with the correct field names and exact source identifiers. Synthetic frontend-only fixtures must not conceal a producer/consumer mismatch. Identify a concrete mismatch before changing behavior; preserve an accurate known-empty versus unavailable distinction and never manufacture source links or narrative claims.

## Work

Read the checked-in live adapter and the frontend parsers. The adapter exceeds the connector's file-content limit; a temporary branch-only contents-read CI audit may print bounded relevant checked-in source functions/lines. It must not connect to any database, model, account or runtime service, and will be removed from final changes. If a contract gap is confirmed, patch the smallest presentation adapter boundary, add producer-derived regressions and real browser scenarios, and retain all existing audit/unit/build/type/browser gates. Do not modify canonical financial/evaluation fixtures to make failures pass.

Only synthetic inputs may be supplied to a pure existing adapter function for contract testing; this is not a live-data claim. Reject malformed IDs, mixed/unknown data and ambiguous sources without inventing a successful record. Preserve the existing read-only provider and date semantics, review draft storage keys, migration behavior and identity safeguards. Record evidence and limitations in the task handoff and PR.

## Exclusions

No main, production deployment, backend financial rules, schema/migrations/seeds, recommendation weights/thresholds, benchmark/evaluation/golden data, orders/broker, dependencies/lockfile, secrets/AWS/accounts or paid model calls. No production database, replacement runtime or automatic retry. No independent review or manual visual approval claim. This task is product data-contract correctness, not investment accuracy or a new research prediction model.
