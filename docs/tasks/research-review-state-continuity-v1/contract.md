# Research review state continuity v1

Base: develop@22727df0a41971b94ea9e061f3387299e5c96c08 (merged PR #45).

## Observed problem

Post-merge Web Product Quality 34085542915, job 101628758735, completed successfully in every required step. Artifact 10005273428 was downloaded and its ZIP SHA-256 was independently recomputed as 9596ed5a303bda18fa96516587028fd3a4deaed330f7f1f9a403687c221901eb, matching GitHub. Actual desktop and mobile-WebKit producer-malformed captures were opened. The top-level error notice is visible, but the rejected claim is labeled only as missing and the rejected source inventory appears as 0 connected documents. Source code inspection confirms current Markdown exports omit structural-data warnings and per-source relationship context.

## Deliverable

Keep invalid, missing and explicit-empty states legible at the point of reading and in the current-basis Markdown export. Describe independently linked company/market documents without implying they replace a rejected research-input inventory. Preserve real valid sources and source selection. Keep malformed values and arbitrary metadata out of visible narrative and export. A stale draft must not acquire current-analysis warnings or sources.

## Boundaries

Presentation-only changes to the notebook, source empty state, Markdown export and focused tests/fixtures. Do not change the serialized ReviewModel, review snapshot algorithm, Draft v1 schema, storage keys, migration policy, source allowlist, API requests, producer contract or SQL. No main, deployment/EC2, production DB, schema/migrations/seeds, financial calculations/weights/thresholds, benchmark/evaluation/golden data, portfolio/order/broker, dependencies/lockfile, credentials/AWS, paid model calls or scheduler changes.

## Acceptance

Field-local and exported messages distinguish invalid/missing/empty; rejected source inventory is not a known-zero total; independently linked sources retain their relationship context and remain usable; legacy and fund behavior stay supported. Current-basis exports retain safe warnings; stale-basis exports exclude current research and warnings. Pure helpers must not mutate models or invalidate existing snapshots. Extend actual-Python-producer tests and browser routes without skipping tests, relaxing assertions, retries or accessibility rules. Run the existing full Web Product Quality pipeline. Inspect final actual desktop/mobile screenshots and report observed evidence separately from unverified live model/production data quality.
