# Review

## Review Notes

- `src/stockanalysis/signal/portfolio_review_report.py`는 read-only SQL report만 추가한다.
- `portfolio-review-run-history` CLI는 portfolio review runs, risk/action counts, latest review, attention items를 JSON으로 출력한다.
- DB schema, portfolio review action rule, coverage gate rule, recommendation score, thesis generation rule은 변경하지 않았다.
- attention item은 실제 조치가 필요한 action만 포함하고, `monitor`는 global action count에만 포함된다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_review_report tests.test_ingest_cli -v`: 38 tests 통과
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 221 tests 통과
- `bash -n scripts/verify_portfolio_review_run_history_report.sh`: 통과
- `bash scripts/verify_portfolio_review_run_history_report.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-run-history-report`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Remaining Review Items

- 실제 cron/automation 연결은 후속 task다.
