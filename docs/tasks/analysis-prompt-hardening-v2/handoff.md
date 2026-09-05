# Analysis prompt hardening v2 — handoff

Baseline develop@04c6c3799625f2d808e256ca219b097ddc990f34. Feature branch codex/analysis-prompt-hardening-v2. The PR is the final integration record for head SHA, CI runs/artifact hashes, merge SHA and post-merge checks.

## Implemented scope

Successful remote runtime uploads include source_validation.py, SEC ai_event_extract.py, news translation.py and news ai_extract.py. SEC validates the declared schema again at canonical candidate construction; positive integer chunk IDs and input-budget types are checked. News Codex inputs are escaped/framed and bounded, while translation and news outputs reject invalid numeric values. News quotes must be literal original title/summary spans across SDK, Codex and final pipeline paths. Existing financial thresholds, storage schemas, provider choice, CLI permissions and fallback status conventions remain unchanged.

Runtime commits: 75342e1d69f27acc5641b443a861c01d5404d2a3 (SEC), 0ecee4db43cfb2eb7f90122a17a372ae5f6ed9a6 (translation), ac5646b102fb3a56bacd64339a44aabebcc8c2bd (news). Tests, CI and review documents follow on this branch. The final head must pass before integration.

## Incomplete broader plan

The equity implementation was prepared and tested locally, but its GitHub upload was denied twice because security status was undetermined. No alternate write path, relocated helper, runner write or permission change applied that blocked code. The final branch must not contain that equity patch or its changed tests. The zero-confidence/defaulting and other equity prompt findings remain open. Do not repeat local broader-patch results as final branch verification.

## Verification and execution limits

The allowed-change local suite has 159 cases from 14 modules: 30 new cases (14 SEC + 16 news/translation), zero failures/errors/unexpected IO, with one optional SDK skip locally. Clean CI installs the already-declared agents extra and requires no skips on Python 3.11 and 3.13. It constructs the actual SDK contract object with Runner mocked. Network/process guards and fake DB executors remain active. See qa.md and review.md for tested boundaries and remaining semantics.

The source archive used for local work came from the read-only export run 33981101116 / artifact 9973769042, ZIP SHA-256 5095d35de8966e0d1efa4a41a12e13ebcf3b93e9069ef8e19bb1edcb8c6592e2. It contained tracked code and test fixtures, not .git credentials or runtime secret files. The temporary export workflow is removed from the final tree. Product writes used the authorized GitHub connector.

## Remaining release work

Literal matching does not prove semantic entailment, faithful translation, causal inference or source truth. SEC raw prompt framing, legacy parser defaults, model-reported usage/reasoning metadata, full-source provenance, future-information leakage and equity hardening remain separately scoped. Stricter validation may reject more old/oversized results; current-workload shadow evaluation is still needed before rollout.

No production deployment, paid/live model invocation, actual DB query, replacement DB, main modification, migration/seed/schema, benchmark/evaluation split or golden-set change, scoring weight, portfolio/order/broker, account/secrets/AWS, scheduler or dependency/lockfile change. No frontend work or new browser run. No independent reviewer approval or world-leading investment-performance claim.
