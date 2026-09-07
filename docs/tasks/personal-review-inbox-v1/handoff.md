# Personal review inbox v1 — handoff

Base develop@b1bbba534d26ee95a1ff612bb66c344107a021b7 (PR #42). Integration: PR #43, codex/personal-review-inbox-v1. This is an investor-facing continuation, not investment scoring, model generation or an operations dashboard. The PR records final observed checks and any integration SHA.

## Implemented user workflow

/research-notes lists existing v1 browser-local drafts. A link from the company notebook and research navigation opens the inbox. Search is literal and memory-only; note/search text is not added to URLs or transmitted to the company API. Directly chosen dates classify entries as overdue/today/planned/undated relative to the displayed device-local day. The day updates on visibility and once per minute; no scheduler, calendar event or reminder is created.

The reader shows saved human judgment, opposition, next questions, manual checks and original identifiers. It does not manufacture a company name, source body, current analysis or a current-snapshot match. Reopening the company's current research uses the existing editor's exact instrument-scoped lookup and snapshot handling. The notes reader remains usable when the company API fails, provided the Next application is reachable. This is not an offline application or service worker.

Only canonical symbol/instrument v1 keys and the existing strict draft schema are accepted. parseDraft's type signature now requires only the identity fields its unchanged runtime validates. The inbox never writes, migrates or deletes notes. Broken, mismatched and unsupported entries remain visible with a raw text export. Reads are bounded at 2000 keys, 200 review keys and 1,000,000 counted characters. Truncated/failed/observably changing reads are partial, not complete or empty. Observed cross-tab changes reload saved data; a removed selected item has no current-record link. This is not atomic storage or immutable history.

Individual Markdown export contains saved human notes and original IDs only, with user text indented literally. Bulk JSON contains all loaded valid notes, regardless of the active search filter, with scope/completeness/problem metadata. It is not an entire-origin backup, account sync, import or automatic restoration. Unreadable raw values are exported separately on explicit request. Shared-device and unencrypted-local-storage limitations remain visible.

## Verification history and recovered failure

Initial 6df0858 CI exposed a search test fixture using MSFT with instrument-aapl; search correctly matched the instrument ID. The fixture identity was corrected without reducing search coverage. Enumeration now also marks a disappearing key index as partial, with a new regression. The following build exposed the throwing test getter's inferred void return; its number return type was declared explicitly.

Head 38aaf74e1a4486f6ee1b547c58c3d4e3d54f4171 was checked by Web Product Quality run 34048669945, job 101528211635. Its logs, retrieved on 2026-09-07, show 443 unit tests / 35 files passed, production build and generated-route typecheck passed, and both dependency audit gates passed. Browser execution ran 102 notebook/inbox cases: 96 passed, 6 failed. All 69 existing notebook cases passed. The five subsequent browser suites were skipped after this failure and are not counted as passed on that revision.

All six failures were the same locator ambiguity across three browser projects: page.getByRole('alert') selected both the real inbox warning and Next's __next-route-announcer__. The failed log contains the expected denied-storage/partial-inventory warning text. This is not evidence of note loss, and the result is not described as a passed suite.

Fix 19a4bc628e352b862210b7d2d675c86c6425b5bc scopes the role locator to the review-inbox boundary. It retains the expected warning text, disabled export when unavailable, 200-entry partial enumeration and completeRead=false assertions, and adds exactly-one/visible warning checks. No .first(), warning removal, application-state change, skip, retry increase or relaxed threshold was used. Only the test file changes in that fix; the existing runtime is unchanged.

Eleven inbox scenarios run on desktop Chromium, mobile Chromium and mobile WebKit alongside all 69 notebook cases. The other five suites remain required. Final expected browser total is 318 (285 existing plus 33 inbox executions); only actual final logs establish the result. Unit cases remain 443, including 37 inbox tests. Final feature-head and post-merge evidence belong on PR #43 to avoid embedding an unverified future SHA here.

## Execution and visual-review limitations

The working container, Python and visible-Python execution returned ClientError in the continuation session. The failed-run ZIP was successfully downloaded through the connector, but a local hash/archive inspection could not execute. Files returned no readable archive content. Therefore neither locally verified ZIP hashes nor manual screenshot inspection are claimed for that archive. No broader runtime/deployment or credentials were introduced to bypass the failure.

Clean GitHub runners execute the real build/browser tests and produce screenshot/trace artifacts. Automated axe/geometry results and screenshot production are distinct from a person inspecting the pixels. If the local runtime remains unavailable, final status must explicitly leave manual visual sign-off open even when automated checks pass. A development integration is not a production/visual release certification. All test notes and company data are synthetic; WebKit device emulation is not physical iPhone verification.

Correction to prior reporting: PR #42 job 101519053984 shows 406 tests across 34 files, including 35 company-review tests. The earlier 409/38 values were inaccurate; the PR #42 correction comment preserves the reporting history. No tests were removed. PR #43's observed baseline is 406 plus 37 inbox cases.

## Exclusions

No main, backend, DB/schema/migrations/seeds, dependencies/lockfile, financial calculations/weights/thresholds, benchmark/evaluation data, portfolio/order/broker behavior, paid model calls, accounts/secrets/AWS, production EC2, scheduler or deployment changes. The temporary credential-free tracked-source/test-runtime export workflow is absent from the final diff. No live financial accuracy, independent reviewer approval, source-entailment certification or account-backed note recovery is claimed.
