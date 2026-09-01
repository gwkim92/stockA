# analysis-integrity-ci-v1 QA

## Local Validation

- verifier shell syntax: passed
- workflow YAML parse: passed
- workflow read-only policy scan: passed
- branch comparison: expected paths only; behind `develop` by 0

## GitHub Actions Validation

PR `#22` generated the first repository workflow run:

```text
workflow: Analysis Integrity
run_id: 33489901070
event: pull_request
runner: ubuntu-latest
conclusion: success
```

Successful steps:

1. Set up job
2. Check out repository
3. Set up Python
4. Install package
5. Verify analysis integrity
6. Post-step cleanup

The verifier on the clean runner performed:

- bounded Python compile;
- source-lineage reconciliation tests;
- readiness-semantics tests;
- readiness-audit tests;
- package entry-point assertions;
- workflow capability assertions;
- diff whitespace validation.

## Final-Head Gate

A task-document or workflow update creates a new PR head and therefore a new run. Manual merge is allowed only after the run associated with the final PR head has conclusion `success` and the PR is mergeable.

## Not Covered

- full `unittest discover`
- Docker/PostgreSQL integration
- live data providers
- Next.js typecheck/build
- browser/API runtime smoke
- scheduler, host, cloud, order, or broker paths
