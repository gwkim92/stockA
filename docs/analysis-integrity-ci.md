# Analysis Integrity CI

## Purpose

This workflow is the repository's first automated pull-request check. Its initial purpose is deliberately narrow: keep the recommendation-weight evidence lineage and readiness boundary reproducible on a clean GitHub runner.

It is not a full repository, database, deployment, scheduler, or trading verification suite.

## What It Checks

- Python package installation from `pyproject.toml`;
- bounded module compilation;
- recommendation weight source-lineage reconciliation tests;
- recommendation weight readiness-semantics tests;
- recommendation weight readiness-audit tests;
- required installed CLI entry points;
- absence of deployment, secret, order, broker, or live-mutation behavior in the workflow and verifier.

## Trigger Boundary

The workflow runs on relevant changes in pull requests and pushes targeting `develop` or `main`, and through manual dispatch. It uses `contents: read` only.

## Explicit Non-Goals

- Docker or live PostgreSQL verification;
- external market/news/filing provider calls;
- EC2, scheduler, or deployment activation;
- secret access;
- portfolio or recommendation mutation;
- order creation or broker submission;
- complete frontend build or browser QA;
- claiming that the complete repository regression suite passed.

## Local Command

```bash
bash scripts/verify_analysis_integrity_ci.sh
```

## Expansion Rule

Additional checks should be added only after they pass deterministically on clean runners. Database, frontend, and deployment checks should remain separate jobs or workflows with explicit runtime contracts.
