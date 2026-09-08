# QA evidence

- Tested app cfa40c90: prior GitHub CI 3/3 success; target-server Next production build/typecheck; isolated backend 72/72.
- Existing live routes: /, /stocks, /stocks/AAPL, /recommendations, /performance, /portfolio/coverage, /research-notes, /data-health, /performance/evaluations: HTTP 200, no checked fatal render marker. data-health took 17.57 seconds; this is not a performance improvement claim.
- Actual browser: history list -> legacy detail, new record detail 1720, mobile 390px. Source is live EC2 through local SSH tunnel, not fixtures.
- Canonical hashes: 1335/1335; actual API metadata validation: 50/50; keyset pages disjoint.
- Price repair: 24/24 real provider requests succeeded within existing budget.
- Price priority extension: 52/52 focused tests (new policy, existing price/backfill/orchestrator), actual PG read-only SQL preview 33 symbols, ADBE/ADI first.
- Full dump decode verifies archive readability, not a rehearsed database restore. No live forward-price mutation or synthetic outcome inserted to manufacture comparison changes.
