# Research payload display contract v1 — handoff

PR #45, base develop@45a33cfd281ce21c31246a039bff93f0924770f7. This repairs stored-data presentation quality, not trading decisions or live model correctness. The PR records final verified head, integration SHA and observed CI outcomes; checkpoint failures below are not final passes.

## Actual finding

The existing producer already converts stored database document IDs to the opaque strings expected by the TypeScript reader. Normal field names match the SQL aliases. The original hypothesis of a normal-field mapping mismatch was not confirmed. Instead, unconditional str conversion allowed malformed stored booleans/numbers/objects to look like narrative strings, while document IDs were not validated before formatting. This was established from code and synthetic inputs, not an inspection of production records.

prepare_equity_display validates title/summary, key_points/catalysts/risks/invalidation_conditions and source_document_ids before legacy formatting. A mixed-invalid list is rejected whole, not salvaged into seemingly complete analysis. Normal strings, explicit empty lists and zero valuation confidence stay intact. Missing fields remain distinguishable through explicit metadata despite compatible public string/list shapes.

Source handling preserves existing raw named aliases such as aapl-2024-10k-20240928, exact positive numeric IDs and their already-prefixed public forms. At most one source-document- prefix is removed before the existing formatter adds it; repeated prefixes, reserved placeholders, malformed IDs and excessive length are rejected. Stored input is never mutated. This is formatting compatibility, not a new source lookup or inferred document association.

The shared _build_stock_equity_research_payload has only three added lines: import/call validation and include data_quality. SQL and all other live_adapter functions are unchanged. It is used by stock, recommendation and thesis responses. Legacy consumers retain safe field shapes; explicit new warnings are added to company workspace/notebook only. This does not upgrade completeness checks across every other screen.

## Consumer and existing notes

The company parser maps flagged values to null (unknown), while a valid [] still means a returned empty list. Corrupt metadata masks the seven affected fields without echoing unknown labels. Metadata-free responses remain supported without claiming producer validation. Complete metadata adds nothing to the review projection, preserving its otherwise-identical analysis-bundle hash; invalid or missing fields deliberately change that displayed basis. Browser draft format, keys and existing explicit migration/reset rules stay unchanged.

Warnings name invalid/unavailable fields in company and notebook pages. They concern data structure, not semantic truth, model confidence or investment approval. Separate event-linked sources remain independent; they are not relabeled as valid research inputs. Old values already persisted as strings cannot be reverse-classified or repaired by this change. Artifact identity and valuation-field validation are outside this task.

## Verification and failures fixed

The Python gate retains every existing frontend live-adapter regression and adds the display/alias tests. The TypeScript contract test and production browser fixture execute the actual Python producer against synthetic inputs, rather than hand-writing its expected output. No database or model is contacted. Correct IDs and claims, rejected lists, missing-versus-empty behavior, note preservation and exports are checked through the existing readers and actual routes.

Head 81fe087 / run 34083569324 exposed three failures: rejected preexisting raw named aliases and double-prefixing of public IDs. Existing stock/recommendation expected-source assertions were not changed. The helper now handles both forms correctly, with extra equivalence, nonmutation and repeated-prefix regressions. That run also recorded three blocked login-status process attempts from unrelated registry tests. The harness now stubs only the exact codex login status boundary as not logged in; all other process/socket IO remains denied and mocked probes are counted separately. It is not a live authentication test.

Refinement implementation is 6ecc6557ac94226fceab52273f3bbc15ba1571ef. Final workflow triggers cover both display test modules as well as the shared producer. All existing frontend unit/build/type/audit and six browser suites remain. Final actual counts and results are required before merging; neither expected totals nor partial checkpoints count as completion.

Local container/Python execution remains unavailable. No local test run, ZIP hash re-verification or manual screenshot inspection is claimed. CI captures prove automated rendering only until pixels can actually be opened. Tests are synthetic and do not certify financial accuracy, current production deployment or physical-device behavior.

## Large-file edit and scope

The 1.1MB adapter exceeded connected file-content reads. The documented branch-only one-shot staging workflow checked the exact original blob and allowed only the known three-line AST function change, created an unreferenced commit, and did not move a branch. The connector inspected its diff before advancing the feature ref. This handled file size, not a security denial. All temporary staging/source-audit workflows are removed from the final tree, including the read-only audit briefly used when resuming the unfinished PR.

No main, production database/EC2, paid model request, accounts/secrets/AWS, deployment/scheduler, DB schema/migration, financial calculations/weights/thresholds, benchmark/evaluation/golden data, orders/broker or dependency/lockfile changes. Additive data_quality is an API payload change, not a DB schema change. No independent reviewer, source entailment, immutable source history or full-backend regression claim.
