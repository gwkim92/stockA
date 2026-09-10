# Handoff — deployment in progress

## Implemented

Feature commit `811ba980` is on develop and was pushed. Follow-up `69d7c608` handles an injected runner result without a stderr attribute. All five adapters, scoped API/browser session, live settings UI and audit are implemented. Local actual browser save/reload and mobile checks passed. The operational default remains Terra until a saved setting is selected.

## Deployment state at 2026-09-10 08:20 UTC

Deployment script `/private/tmp/stocka-deploy-model-settings.py` validated IMDS personal account `115623963546` / instance `i-029d51b163fb07b61`, backed up env files under `/opt/stockanalysis/runtime/model-settings-20260910`, and pulled `811ba980` into `/opt/stockanalysis/app` develop.

It started a separate build under `.../model-settings-20260910/build`. Dependencies are hard-linked from the existing node_modules, and live `.next` is untouched until build completion. Node heap was capped at 768MiB, but the 2GiB server became unresponsive to SSH and the local web tunnel during the build. No `built` or `activated` result has been observed. **Do not claim successful production deployment.** Memory pressure is suspected, not yet confirmed by a remote readback. No AWS instance setting has been changed.

The existing SSH control master `/private/tmp/stocka-runtime-20260910.sock` remains locally alive. A remote diagnostic command and a command to add temporary 2GiB swap at `.../model-settings-20260910/build.swap` are pending through that connection. Their completion has not been observed; do not duplicate the swap operation blindly. The original deployment SSH session may still resume and activate `811ba980` if the build finishes.

The news-intraday service had completed (`inactive/dead`, last status 0) before build activation was attempted. At last confirmed resource readback: 1,913MiB RAM, 1,086MiB available, no swap, 6.5GiB disk free. SSH banner exchanges subsequently timed out; the local web tunnel returned no bytes in 8 seconds.

Chrome is open to the personal instance console but AWS requested login. The user was asked to sign into personal account `115623963546` so console state/recovery can proceed. Do not use the locally configured company AWS CLI or act in account `061051252914`.

## Next actions

1. Recover server responsiveness using the existing SSH connection or the user's authenticated personal EC2 console. Verify account before any AWS action. Stop only the task's build process if reachable; a console reboot is a fallback if the instance is unresponsive.
2. Inspect actual build/process/env/`.next` state before retrying. Read `previous-commit.txt`, server-only `build.log`, and presence of `deployment.json` / `previous-next`. Preserve runtime backups and business DB.
3. Ensure temporary build swap is active before any further server build, or build an equivalent Linux artifact off the production host. Use a bounded build and avoid simultaneous heavy processes. Remove temporary swap only after services are healthy and sufficient memory is free.
4. Bring develop to the latest committed fix. Finish model store initialization/catalog refresh and set the same `STOCKANALYSIS_AI_MODEL_SETTINGS_PATH` in data-operations.env and frontend-api.env. Existing CLI env pins Terra and must remain unchanged.
5. Verify API/web, issue a one-use model-manager code, unlock the user's in-app browser, save a translation-only Luna override through the UI. Run `/private/tmp/stocka-web-model-smoke.py` on the server with the application Python: it uses a synthetic news input and no business DB writes. Verify observed model, then restore inherited Terra via UI and verify readback.
6. Capture production desktop/mobile UI, confirm scopes/audit/session persistence and final Terra default, record remaining unobserved task executions, update QA/handoff, and commit evidence.

## Verification

123 targeted Python tests and 14 frontend tests passed; Next typecheck/build passed. The original prompt CI found a missing stderr field in a mocked cycle runner; `69d7c608` fixes it. Local prompt verification then passed 272 tests with one SDK availability skip (local venv has no agents extra). CI's SDK-installed result is still to be checked for the fix. A follow-up adds model settings tests to that continuous regression suite.

Local test-only services: API 127.0.0.1:8795 and Next 127.0.0.1:13003, SQLite `/private/tmp/stocka-model-settings-qa.sqlite3`, Playwright session `stocka-models`. Its saved Luna override is local QA data, not a production setting. Temporary screenshots `/private/tmp/stocka-model-settings-{desktop,mobile-top,mobile-control}.png` were visually inspected.

Unrelated pre-existing `docs/tasks/runtime-deploy-20260908/handoff.md` and prior-turn runtime-evidence-recovery docs remain uncommitted and must be preserved.

## Recovery preparation follow-up

Latest implementation/build-support commit is `5e549e38`. The fixed provider observation passed SDK-installed CI `34454568956`. Model settings tests were added to continuous prompt regression (277 local tests, one missing-SDK skip). Web Runtime Artifact CI `34454905757` succeeded and its artifact was downloaded and hash/path verified: `artifacts/ai-model-settings-v1/linux-runtime/`, build ID `Hn2ruTFaLHoyn1uX8YDDc`. This removes the need to build again on the small EC2 host.

Prepared activation script `/private/tmp/stocka-activate-model-artifact.py` verifies artifact digest, build ID, package lock and source-tree equivalence, refreshes the authenticated model catalog, initializes the shared Terra setting if needed, and switches `.next` with backups and timer restoration. It is **not executed**. It expects the verified artifact directory at `/opt/stockanalysis/runtime/model-settings-20260910/artifact`. Inspect the old deployment process and server state first; do not run it alongside the old build. The script allows documentation-only commits newer than the artifact, but rejects runtime/web source differences.

The existing multiplexed diagnostic channel eventually failed with broken pipe; a fresh SSH attempt still timed out during banner exchange. The pending swap command has not reported success. The original deployment's remote state remains unknown. The AWS login form initially had the company account prefilled; it was changed to personal account `115623963546`, and no sign-in or AWS write action was performed. User login remains required for console recovery.

The two remaining task SSH clients (deployment and queued swap) were terminated locally to prevent a delayed activation after handing off. This does **not** prove the remote build process stopped. Inspect/stop the task-specific build or reboot the verified personal instance if it remains unresponsive. The original script prints and flushes a build-completed result before any activation; its stdout transport is now closed. No further automatic deployment command is pending locally.

Copies of the prepared activation and synthetic smoke scripts are retained in `artifacts/ai-model-settings-v1/activate-model-artifact.py` and `web-model-smoke.py`. They have not been executed in production. Latest CI `34454905672` (all four prompt/DB jobs) and `34454147709` (full web quality/browser flow) passed. Runtime recovery, model catalog/store activation, owner browser session and real model selection verification are the remaining work.
