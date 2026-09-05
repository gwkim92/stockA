# Frontend dependency remediation v1

User request: implement the two next tasks: dependency security remediation and an investor-readable recommendation detail. This task addresses issue #26 only; detail changes belong in a separate PR.

## Scope

Start from develop@ac8b552d5ed7b1e92307a3bf55f908297421eb21. Recheck the npm audit and dependency paths, upgrade Next from 16.2.9 to the verified upstream 16.3.4 tag, and update only affected transitive dependencies within parent ranges. Upstream packages/next/package.json at v16.3.4 pins postcss 8.5.23 and allows sharp ^0.35.4. Preserve React 19.2.5 and unrelated direct dependency declarations. Do not run audit fix --force or bypass peer constraints.

The sandbox cannot resolve GitHub/npm. A temporary, branch-only preparation workflow may regenerate package.json/package-lock.json on a clean GitHub runner and commit ONLY those two files to codex/web-dependency-remediation-v1. It must not run on PRs/forks or accept arbitrary inputs; checkout credentials are not persisted, the default repository token is exposed only in the final git-push step, push is non-force, and no production secrets are used. Remove this temporary workflow before merge. Archive the exact tracked web source and audit/diff evidence for local inspection.

## Acceptance

A lockfile diff inventory and before/after full and production audits are preserved. npm ci, all frontend tests, Next production build, generated-route typecheck, desktop/mobile home browser tests must pass on the committed candidate. Make high/critical dependency audit failures gating rather than diagnostic-only. No passing check is a blanket claim of exploitability assessment or future vulnerability absence.

## Boundaries

No backend, database, migrations, investment score/weight/benchmark, trading, scheduler, deployment, account or production-credential changes. No new database. Review and merge through develop; leave main and deployed EC2 unchanged.
