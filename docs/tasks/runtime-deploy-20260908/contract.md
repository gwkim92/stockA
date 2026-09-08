# Runtime deployment contract

User authorized proceeding with failure diagnosis, backup/schema checks, latest develop deployment and real-data verification on 2026-09-08.

Target: personal AWS account 115623963546, us-east-1, EC2 i-029d51b163fb07b61, SSH 3.211.40.142, /opt/stockanalysis/app. Deploy develop only. Starting server HEAD 366abe812d20fbe059ad5a5b62c501c0107ee9ae; intended tested application HEAD cfa40c905fd3a538caf6292eafe84bacfc25e289.

Scope: inspect actual job failures; preserve server untracked files; make and verify local-to-server DB/code/build recovery artifacts; apply the existing additive migration 0035 if missing; update dependencies/build; restart web/API; validate actual API and UI. Diagnose provider/auth/freshness failures and apply only supported, bounded operational recovery. No new AWS resources/security-group writes, no secret disclosure, no scoring/weight/benchmark policy changes, no broker/order writes. Do not manufacture historical snapshots or generate paid model work merely to turn health green.

Acceptance: exact deployed ref and built artifact recorded; DB backup verified; applied schema checked; web/API healthy and new evaluation routes work against live data; remaining operating failures accurately identified. Evidence and rollback procedure in handoff, qa and review.

Diagnosis extension: the persistent daily watchlist contains only six stocks while 32 symbols have active recommendations. Add an opt-in configured-plus-active watchlist policy to the existing daily runner, ordered by oldest stored price; enable it on this runtime. Keep daily budget 24, per-run cap 6, provider, scoring and timers unchanged. Missing symbols are prioritized without altering the configured CSV. This fixes repeated omission rather than treating a one-time backfill as durable recovery.
