# Research payload display contract v1 — handoff

PR #45, base develop@45a33cfd281ce21c31246a039bff93f0924770f7. This repairs stored-data presentation quality, not trading decisions or live model correctness.

## Actual finding

The existing producer already converts stored database document IDs to the opaque strings expected by the TypeScript reader. Normal field names also match the SQL aliases. No normal-source-ID mismatch was demonstrated. The problem is the producer's unconditional str conversion for scalar-list contents: malformed stored bool/number/object inputs can be exposed as apparently ordinary narrative strings, and source lists did not validate positive database identifiers. Source and code inspection, rather than a production DB query, established this behavior.

The new prepare_equity_display helper validates title/summary, key_points/catalysts/risks/invalidation_conditions and source_document_ids before the existing conversion. Lists containing an invalid item are rejected as a whole, not partially salvaged. Normal strings/lists/positive exact numeric IDs, empty values, field names and valuation content remain. The helper copies the input and does not write a database. Absence is not an empty-list assertion: metadata identifies invalid versus unavailable fields while keeping existing API list/string shapes for legacy consumers.

The existing shared _build_stock_equity_research_payload is amended by exactly three lines: invoke the helper and return data_quality. Its SQL and all other live_adapter functions are unchanged. This shared producer also serves recommendation/thesis responses; their legacy consumers receive safe existing shapes, but this PR adds explicit warnings only to the company workspace and notebook. It is not a full redesign of every research screen.

## Consumer and saved-draft compatibility

The company parser projects flagged input fields to null, which the existing reader treats as unavailable. A actual [] remains empty. Malformed metadata masks narrative/source fields and does not echo arbitrary names into warning copy. Metadata-free legacy payloads are supported without inventing a validation claim. Complete metadata adds no new property to the displayed review model, so it does not invalidate a previously saved otherwise identical analysis-bundle hash. Partial/invalid fields change the displayed basis and continue to use the established explicit stale-note migration flow. Draft formats/storage keys are unchanged.

The shared notice makes invalid/missing fields visible on company and notebook screens. This is structural integrity, not semantic verification, financial confidence or claim-level evidence. Separate direct/background event sources remain independent of a rejected research inventory; they are not silently reclassified as the missing research input list. The provider label, financial outputs and source-policy blocker remain separate.

## Verification

Python tests use synthetic records. TypeScript tests spawn the actual checked-in Python producer with sockets/subprocess execution denied inside the generator, then consume its output through parseCompany and reviewModel. Production browser fixtures use that same real producer output for additional valid/malformed/partial/empty scenarios; existing healthy fixtures and financial/API example files are unchanged. Browser cases require the correct opaque source to be fetched, no invented links for rejected inventories, distinct empty/missing/invalid states and preservation of the personal-note editor.

The workflow retains all existing unit/build/type/audit and six browser suites, and adds the display-contract and existing live-adapter Python regression with external IO blocked. Exact final results must be read before being reported. A partial checkpoint is not final-code validation. No local test/build/browser execution or manual screenshot inspection is claimed; container/Python remain unavailable. New screenshots are evidence of automated rendering only until their pixels can be opened.

## Large-file edit and temporary permission

The 1.1MB adapter exceeded the connected content read limit. A documented branch-only one-shot CI staging task validated its original blob and an AST diff allowing only the known function, created an unreferenced Git commit object, and printed the commit/blob identifiers without secrets. The connector fetched and checked the exact three-line diff before advancing the feature branch. This exception handled a file-size limitation, not a bypass of a security denial. Both temporary audit/staging workflows are deleted from the final tree. Remaining edits are regular connector operations.

## Exclusions

No main, production database/EC2, paid model requests, account/secrets/AWS, deployment/scheduler, schema/migration, financial calculations/weights/thresholds, benchmark/evaluation/golden data, order/broker or dependency/lockfile changes. The new additive display metadata is an API payload change but not a DB schema change. Artifact identity, valuation-sensitivity validation, full historic source versions, old stringified data repair, and semantic source entailment remain outside this bounded change. No independent reviewer or live financial accuracy claim.
