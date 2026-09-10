# Handoff — deployed and verified

## Current result (2026-09-10 09:13 UTC)

The feature is live on personal EC2 `i-029d51b163fb07b61` / `115623963546` / us-east-1 / `3.211.40.142`. Runtime source is develop `f9f1d5ee0c5fca56b8ff8ddbe83e867ab1f87135`. The Linux web artifact was built from `5e549e384ff60611e88b4dd22fe62013cbb7d7fa`; later changes are backend/tests/docs only, with the web source unchanged. Build ID: `Hn2ruTFaLHoyn1uX8YDDc`.

Open `http://127.0.0.1:13309/admin/ai-agents` through the local SSH tunnel. User Chrome tab `1527793421` has a redeemed model-manager session, verified after reload, expiring 2026-10-10 18:05:53 KST. Select the common default or a workload model, then save. Model changes apply to the next invocation. The session only permits model settings changes.

Final saved configuration: revision **2**, default **gpt-5.6-terra**, **no overrides**. All five workloads inherit Terra. Catalog has seven visible models: Astra, Sol, Terra, Luna, Daybreak Blue, GPT-5.5, Spark. Stored at `/opt/stockanalysis/runtime/ai-model-settings.sqlite3`, mode 0600, with the same path configured in frontend-api.env and data-operations.env. Existing CLI Terra pin and provider settings were preserved.

## Actual browser-to-model verification

1. Chrome initially showed read-only controls. Redeeming a one-use code enabled model controls.
2. Chrome saved only news Korean translation to Luna (revision 1).
3. The real project translation adapter, with a synthetic news input and no explicit model argument, returned `gpt-5.6-luna`, CLI reasoning `none`, Korean title/summary, validated grounding, exit 0, latency 5907ms at 09:09:21 UTC.
4. Chrome restored translation to inherited Terra (revision 2).
5. The same adapter returned `gpt-5.6-terra`, reasoning `none`, validated Korean output, exit 0, latency 4239ms at 09:10:43 UTC.
6. Reload retained the owner session and revision 2. The UI showed actual Terra success and both audit entries. Desktop 1440px and mobile 390px had no horizontal overflow.

Both successful synthetic checks wrote zero business DB rows. Runtime observation records are stored separately. An initial test harness attempt called the provider but then failed in its recording wrapper due to a local variable shadow; it is retained as a failed adapter observation. The harness was fixed before the two successful checks. This was not a production adapter variable error.

Live API `history_available=true` includes prior DB records for translation #40826, news extraction #40839, cycle summary #40770 and equity research #39862. The last equity record is failed and remains visible. SEC extraction has no matching business invocation. These older `codex-cli-default` records do not prove an actual underlying model. The other four adapters were covered by integration tests; they were not forced to execute externally in this task.

## Recovery and deployment evidence

The first server-side Next build under `/opt/stockanalysis/runtime/model-settings-20260910/build` caused SSH/web unresponsiveness before activation. Memory pressure is suspected; no OOM kernel entry was found after recovery, so the root cause is not proven. The old live `.next` was preserved (build ID `ACSruGlBuP3B8ZnxoAOea`), the build log stopped at compilation, and no old activation result or task swap file was present. Closed local deployment/swap transports were not assumed to stop the remote process.

After the user logged into Chrome, account/instance/EIP were verified in AWS UI. One EC2 reboot was requested; SSH and both original services recovered at 09:03:29 UTC, uptime one minute, available memory 1353MiB. No instance type, EIP, security group, IAM, billing or company-account resource was changed. No second server build was run.

The verified CI artifact was copied to the task runtime directory. The activation helper checked IMDS identity, SHA-256, source equivalence, package lock and build ID, retained `.next` and env backups, initialized/refreshed model settings, switched the artifact and restored all 13 previously active timers. Final health at 09:12:57 UTC: all three API/web services active; API ready, web home, model page on ports 3000/13000 all HTTP 200; shared settings path and mode confirmed. A final backend-only fix cast PostgreSQL JSON to text so the existing pool executor could parse business history. Its six focused tests passed locally and on EC2; CI passed.

## Artifacts and follow-up boundaries

- Sanitized final evidence: `artifacts/ai-model-settings-v1/production-verification.json` (ignored local artifact), also `/opt/stockanalysis/runtime/model-settings-20260910/final-verification.json` on server.
- Browser captures: `artifacts/ai-model-settings-v1/production-*.png`.
- Linux artifact: `artifacts/ai-model-settings-v1/linux-runtime/`; SHA-256 `08886f9e8e1efc897c2f2d4c744db37dcb3e9024acd3a8179362725c86b37b0a`.
- Backup/build/activation evidence remains under `/opt/stockanalysis/runtime/model-settings-20260910/`. Do not rerun the original build/deploy script. Use externally built Linux artifacts for this small host.
- Local tunnel master: `/private/tmp/stocka-model-live-20260910.sock`, localhost 13309 to server 3000. Model writes require this localhost tunnel or HTTPS; public HTTP model writes are intentionally rejected.
- New browser/device access requires a fresh one-use `python -m stockanalysis.ai.model_settings grant-access` code under the operational environment. Codes and sessions are stored only as hashes.
- Provider-side internal routing, all five workloads' post-change business acceptance, scheduler catch-up outcomes and public-IP network reachability were not inferred from these checks. Thirteen active timers prove restoration, not successful future executions.
- Recommendation weights, benchmarks, evaluation datasets, business schema and order execution were unchanged.
- Pre-existing runtime-deploy-20260908 and runtime-evidence-recovery-20260910 document changes remain uncommitted and preserved.
