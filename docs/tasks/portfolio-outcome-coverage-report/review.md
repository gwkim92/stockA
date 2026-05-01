# Review

## Review Notes

- `src/stockanalysis/performance/coverage.py`는 read-only SQL lookup과 summary builder만 추가한다.
- DB migration, attribution calculation, recommendation score, thesis generation rule은 변경하지 않았다.
- CLI는 `portfolio-outcome-coverage-report` JSON 출력만 담당한다.
- status 분류는 position snapshot을 기준으로 `covered`, `missing_outcome`, `missing_thesis`, `missing_weight`를 반환한다.
- weight coverage는 known weight 기준으로 계산하며, missing weight가 있으면 cash weight를 `null`로 둔다.

## Verification Evidence

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_outcome_coverage_report tests.test_ingest_cli -v`: 41 tests 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 213 tests 통과
- `bash -n scripts/verify_portfolio_outcome_coverage_report.sh`: 통과
- `bash scripts/verify_portfolio_outcome_coverage_report.sh`: 승인된 Docker 접근으로 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-outcome-coverage-report`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Remaining Review Items

- 실제 운영 스케줄러 또는 dashboard 연결은 후속 task다.
