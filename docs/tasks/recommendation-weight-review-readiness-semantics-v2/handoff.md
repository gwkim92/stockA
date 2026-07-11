# recommendation-weight-review-readiness-semantics-v2 Handoff

## Status

- completed: local implementation, `develop` push, EC2 deployment, shadow dry-run/execute, API comparison, and runtime smoke are complete.
- current branch: `develop`.
- base commit: `6a397511`.
- deployed commit: `83e28638` on `ec2-user@3.211.40.142` in personal AWS account `115623963546`, instance `i-029d51b163fb07b61`, region `us-east-1`.

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

## Live Shadow Result

- automatic and pinned dry-runs selected readiness `28`, quality `801`, outcome `692`, and `Long Term Paper` portfolio feedback `697`; 30/90/180/365 horizon evidence and the pinned semantics hash were stable.
- execute completed with `pipeline_run_id=10991`, `eval_run_id=809`, semantics SHA-256 `10e8f2a4b91de235132cbb1d98c35e9f267db6d0a9cda7c0d1951c26f5cc6fcc`.
- decision is intentionally `evidence_incoherent_fail_closed`. Readiness `28` still references quality `26` and outcome `27`, while the latest selected quality/outcome are `801`/`692`; outcome `692` also lacks the required cohort-filter attestation and its nested quality differs from quality `801`.
- the result was not made green by rerunning or rewriting legacy artifacts. `manual_review_eligible=false`, every approval/pilot/mutation/order/broker permission is false, and `order_boundary=read_only_no_order`.
- pre/post API comparison proved the v1 payload hash `0312694bead69a86e40a7c784c4ecb3ba95ca407d5d179811040960b08660707` and `open_gates` hash `ab9cffd582503fdc679f4201e761211b7e86fbca2d399d8a7b3be7d2f2c63699` were unchanged. The v2 sibling did not enter `open_gates`.

## Verification Evidence

- task verifier: 40/40 passed.
- adjacent readiness/calibration/CLI/data-health regression: 251/251 passed.
- frontend: Vitest 25 files / 59 tests passed; TypeScript and production build passed.
- frontend API contract, project roadmap, CLI help, compileall, migration diff, and diff checks passed.
- full Python discovery ran 1,300 tests and exposed 5 unchanged out-of-scope failures in data-operations env-readiness expectations: four errors and one CLI assertion caused by missing TossInvest test variables. The failing implementation/tests are byte-for-byte unchanged from base `6a397511`; this task does not alter them.
- EC2: Python compile passed; direct task regression 40/40 passed; CLI has no approval/mutation flags; Next typecheck/build passed.
- EC2 services `stockanalysis-frontend-api.service`, `stockanalysis-web.service`, and `stockanalysis-web-public-13000.service` are active. FastAPI `__ready` is `ok/live/read-token/read_only_no_order`; `/` and `/data-health` returned 200 on ports 3000 and 13000.
- the shell verifier itself stopped because EC2 lacks `rg`; no package was installed. Its 40 Python/CLI checks were executed directly with EC2-available tools and passed.
- persisted rows were read back: pipeline `10991` is `succeeded`; eval `809` has the expected v2 eval/dataset/model identity.

## Exact Next Step

- exact next step: open a read-only `recommendation-weight-review-source-lineage-reconciliation-v1` task to define how one canonical readiness→quality→outcome chain is selected and how cohort filters/nested quality are versioned. Do not rerun legacy artifacts merely to clear blockers. After that, add prospective row identity/component snapshots, feedback deduplication, and an approved freshness policy before drafting a separately approved pilot packet.

## Guardrails

- No weight/pilot proposal, scoring mutation, portfolio mutation, order, broker submit, schema migration, scheduler change, or authoritative cutover. The only live data writes were pipeline lifecycle `10991` and append-only eval `809`.
- Existing v1 artifacts and consumers remain unchanged.
- Keep existing untracked QA directories unstaged.
