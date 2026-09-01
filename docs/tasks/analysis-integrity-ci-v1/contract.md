# analysis-integrity-ci-v1 Contract

## Goal

Introduce the repository's first GitHub Actions check as a conservative, deterministic analysis-integrity gate for pull requests and pushes targeting `develop` or `main`.

## Scope

- `.github/workflows/analysis-integrity.yml`
- `scripts/verify_analysis_integrity_ci.sh`
- `docs/analysis-integrity-ci.md`
- this task directory

## Required Behavior

- run on relevant pull requests, pushes, and manual dispatch;
- use read-only repository permissions;
- install the Python package from `pyproject.toml` on Python 3.11;
- compile the bounded analysis lineage/readiness modules;
- execute focused source-lineage, readiness-semantics, and readiness-audit tests;
- validate required installed CLI entry points;
- reject workflow or verifier text that introduces secrets, deployments, brokers, orders, or mutation execution;
- avoid Docker, live PostgreSQL, network data providers, schedulers, deployments, and broker integrations.

## Invariants

- no production runtime, schema, recommendation score, portfolio, scheduler, deployment, or broker file changes;
- no write permissions, secrets, environment credentials, service containers, or live APIs;
- CI failure must not trigger an automated mutation or deployment;
- initial CI is intentionally narrow and must not be represented as full repository verification.

## Acceptance Criteria

- workflow YAML is syntactically valid and uses pinned major action tags;
- path filters include the workflow, verifier, Python package metadata, relevant analysis modules, and tests;
- focused verifier passes locally;
- the pull request created by this task produces a GitHub Actions workflow run;
- the workflow result and any failure are recorded in QA and handoff before merge;
- manual merge only after the workflow is green and PR is mergeable.
