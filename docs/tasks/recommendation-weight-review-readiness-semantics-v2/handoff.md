# recommendation-weight-review-readiness-semantics-v2 Handoff

## Status

- completed: local deterministic shadow semantics, append-only runner/CLI, strict data-health projection, concrete frontend DTO/defaults, tests, verifier, and roadmap/API-contract updates are implemented.
- current branch: `codex/recommendation-weight-review-readiness-semantics-v2`.
- base commit: `6a397511`.
- deployment state: not pushed, not deployed, not executed against the live DB, and not EC2-smoked.

## Starting Evidence

- Legacy v1 equates blocker-free evidence with `manual_weight_review_allowed=true` but consumes no explicit user-approval record.
- Outcome calibration can report ready from aggregate outcomes while some selected horizons remain immature; its per-horizon rows are not part of the v1 decision.
- The latest explicit 2026-07-04 decision says the pilot was not started and portfolio feedback still blocks weight review.
- Legacy artifacts do not attest stable row-level sample identity, feedback deduplication, approved horizon policy, immutable component snapshots, or an approved freshness policy.

## Implemented Result

- New eval/dataset: `recommendation_weight_review_readiness_semantics_v2` / `recommendation-weight-review-readiness-semantics-v2`.
- Mode remains `shadow_read_only`, `authoritative=false`; execute writes only the pipeline-run lifecycle and one append-only `ai.eval_run` artifact.
- The source chain binds readiness, quality, outcome, and exactly `Long Term Paper` portfolio feedback; it validates required counts, row partitions, recommendation×horizon shape, price-gap fields, cohort filters, source references, nested quality, and future dates.
- Legacy thresholds may produce `threshold_evidence_ready=true`, but `manual_review_eligible=false` remains enforced because row identity, feedback deduplication, component snapshot versioning, horizon policy, and freshness policy are un-attested.
- The API sibling reconstructs exact nested allowlists. Authorization, pilot, weight, portfolio, order, and broker fields are fixed to the blocked state and raw nested aliases are discarded.
- Existing v1 readiness, outcome router, open-gate, scoring, portfolio, and order consumers are unchanged.

## Verification Evidence

- task verifier: 40/40 passed.
- adjacent readiness/calibration/CLI/data-health regression: 251/251 passed.
- frontend: Vitest 25 files / 59 tests passed; TypeScript and production build passed.
- frontend API contract, project roadmap, CLI help, compileall, migration diff, and diff checks passed.
- full Python discovery ran 1,300 tests and exposed 5 unchanged out-of-scope failures in data-operations env-readiness expectations: four errors and one CLI assertion caused by missing TossInvest test variables. The failing implementation/tests are byte-for-byte unchanged from base `6a397511`; this task does not alter them.

## Exact Next Step

- exact next step: deploy and execute this v2 only as a shadow audit, compare the stored artifact with v1, and do not cut over a gate. Then add prospective row identity/component snapshots, feedback deduplication, and an approved freshness policy before drafting a separately approved pilot packet.

## Guardrails

- No weight/pilot proposal, scoring mutation, portfolio mutation, order, broker submit, schema migration, authoritative cutover, or EC2 write.
- Existing v1 artifacts and consumers remain unchanged.
- Keep existing untracked QA directories unstaged.
