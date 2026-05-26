# reported-segment-parser-quality-v1 Review

## Review Summary

- scope check: within bounds. The task expands deterministic parser coverage for a real linked Apple 10-K candidate.
- schema check: no migration is introduced; existing `research.segment_footnote_evidence` storage is reused.
- scoring check: no recommendation score, score component weight, benchmark, or broker/order mutation is introduced.
- parser check: the new path handles transposed reportable segment tables and excludes aggregate/non-operating columns.

## Issues Found

- Initial transposed parser logic overparsed year/change/date tables when applied to the real Apple 10-K. The implemented detection now requires a singleton filing-year row before the segment header row, which removes those false positives in the copied EC2 artifact check.
- Initial EC2 smoke after parser expansion exposed a candidate selection issue: the parser attached rows to a `shares_outstanding` point-in-time period. The candidate query now prioritizes statement periods with revenue, operating income, or net income, and the upsert removes stale reported segment metrics for the same source document when period alignment changes.

## Residual Risks

- The parser remains deterministic and conservative rather than a full SEC/iXBRL taxonomy parser.
- Other issuers may use different segment layouts requiring additional parser patterns.
- SOTP still needs a follow-up task to consume reported segment metrics as explicit segment-level valuation input.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis` passed with `Ran 34 tests`.
- `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` passed with `Ran 122 tests`.
- `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- `bash scripts/verify_project_execution_roadmap.sh`, AWH verify, `git diff --check`, and Python 3.13 full suite passed.
- Python 3.13 full suite: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` passed with `Ran 971 tests`.
- Manual local parser check against `/private/tmp/aapl-20250927.htm` returned exactly 10 Apple reportable segment rows and no Corporate/Total rows.
- After statement-period candidate correction, professional analysis tests, focused regression, `compileall`, roadmap verification, AWH verify, Python 3.13 full suite, and `git diff --check` passed again.
- EC2 parser smoke on commit `cdcc1d5` passed with `run_id=1059`, `reported_segment_metric_count=10`, `removed_stale_metric_count=10`, and `recommendation_scoring_mutated=false`.
- EC2 DB verification shows exactly 10 AAPL reported segment rows on `period_end=2025-09-27`, with no stale `2025-10-17` rows.
