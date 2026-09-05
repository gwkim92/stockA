# stockA product review — 2026-09-05

## What this product is

The intended product is a long-horizon investment research and review workspace. It continuously connects macro/policy/technology/industry/company changes to independent theme cycles, company investment theses, research candidates, existing holdings, and measured decision outcomes. It starts paper-first rather than with autonomous order execution.

The original source is `docs/project-foundation.md`. Its horizons are approximately three months, three-to-twelve months, and one year or longer. Its success criteria are better explanations and reviewable decisions, not merely a ranked ticker list or a large number of passed operational gates.

The investor should be able to answer:

1. Which themes or sectors changed, and what evidence supports that interpretation?
2. Why is this company a candidate, what catalysts matter, and what would invalidate its thesis?
3. Does the original case for a holding still apply, and what needs review now?
4. Did past judgments work relative to their benchmark, horizon, and risk?

## Corrected assessment

The repository is not just a fixture prototype. It contains FastAPI/live PostgreSQL adapters, Next.js research pages, professional financial/valuation/fund analysis, AI provider/evidence paths, portfolio feedback and performance workflows, and recorded EC2/systemd operating evidence. `AGENTS.md` and the execution roadmap contain dated implementation and runtime records. These establish historical progress, not current remote service health.

The earlier summary incorrectly treated AI, frontend, and operations as largely unimplemented and treated a missing stockA Neon connection as a general development blocker. The documented operating environment includes EC2. A connector not exposing that environment does not prove that the database does not exist, and a new Neon database is not a prerequisite for repository/UI improvements.

Recent PRs #21-24 improved source lineage and weight-review auditability. Keep those safeguards, but do not let further nested readiness/approval/observation wrappers replace the investor's research workflow. This review intentionally supersedes that narrow immediate priority for the current frontend task; it does not approve trading, weight changes, or infrastructure writes.

## Code-backed gaps

### Home reliability and evidence presentation

At baseline `7907caa3dbcd2d571bb066f173e7ec9225409284`, `apps/web/src/app/page.tsx` depended on seven backend requests through nested `Promise.all` calls. Any rejection discarded the whole page. The fetched health payload was unused. Missing failed-job counts were converted to zero and could produce a normal-status claim. Trading readiness was displayed as available for every non-`blocked` string, including unknown values. A paper-input flag took precedence over a source blocker. Snapshot counts were described as today's new evidence without a comparison establishing novelty.

PR #25 replaces this with four independently bounded read-only feeds: cycle states, recommendations, news clusters, and holding-review summary. HTTP/transport/invalid-body/time-budget failures stay local to their section. Unknown numbers remain unknown. Successful empty data is different from unavailable data. Unidentifiable rows fail that feed instead of disappearing into a misleading empty list.

### Research and operating state separation

The home now prioritizes observed cycle transitions, company judgment documents, source news, holding review, and a link to performance. It preserves backend recommendation order. The summary is compact; detailed connection information is collapsible after the research sections. Operational records remain in `/data-health`.

API analysis dates are visible and never replaced by response-generation timestamps. A matching analysis date is not proof that every underlying price, filing, or news source is fresh. Detailed source provenance remains necessary. This is presentation labeling, not a new approved investment freshness policy.

### Analysis exists; ranking quality is a separate question

`src/stockanalysis/signal/recommendation.py` still contains the bootstrap score version, momentum from `return_since_first_observation`, a short-term component from `return_1d`, and rank/cycle components. It also contains macro-flow integration and zero-weight hierarchy/broker diagnostics. Therefore the old four-component description is not the complete current model, while the horizon consistency of the baseline remains a valid concern.

Professional reports existing does not establish that their information improves ranking, and software tests do not establish investment edge. Do not increase weights to make that claim appear true. First define comparable fixed lookbacks, point-in-time inputs, missing-data behavior, benchmark-relative evaluation, and an isolated shadow comparison. Preserve existing evaluation splits/benchmarks unless a separate change explicitly defines the new comparison.

### Dependency maintenance

The first full frontend CI install reported eight high-severity npm audit entries. This task did not introduce package/lockfile changes. CI now preserves an audit JSON inventory rather than hiding the warning or running `npm audit fix --force`. A green product test workflow is not security release clearance. Exact affected-package analysis and compatible patch validation are separate pre-deployment work.

## Next development order

1. Finish and verify the resilient investor home (PR #25).
2. Consolidate the company decision document: investment claim, primary evidence, valuation assumptions, counter-case, invalidation conditions, and next review date should be readable together. Reuse existing analyses instead of creating another audit subsystem.
3. Add meaningful change views for recommendations/theses/holdings using actual prior snapshots. Do not label a current snapshot as a change report.
4. Evaluate fixed-horizon features in an isolated comparison before altering live scoring weights. Measure coverage and risk as well as returns.
5. Resolve dependency advisories and verify deployment against the existing intended environment; do not provision a replacement database just because the current connector cannot reach EC2.

## Verification interpretation

The new frontend workflow runs the repository's frontend unit tests, production build, route-aware type check, and desktop/mobile Chromium tests. The browser suite uses a local HTTP fixture server and dummy credentials only, and includes partial/full outage, slow JSON body, historical evidence, missing counts, empty lists, link targets, overflow, and scoped accessibility checks.

These checks prove the UI's tested behavior. They do not prove current EC2 availability, live data accuracy, all deeper route behavior, investment profitability, or permission to trade. No production deployment, database query/write, migration, scoring/weight change, or broker action is part of PR #25.
