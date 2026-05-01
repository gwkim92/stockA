# Review

## Review Notes

- `portfolio-remediation-ticket-report`는 persistent ticket을 조회하는 read-only report다.
- DB schema, review action rule, recommendation score, thesis generation, attribution, performance outcome calculation은 변경하지 않았다.
- 기본 status filter는 `open`이고, `--status all`로 전체 상태를 조회한다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_ticket tests.test_ingest_cli -v`: 통과
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 234 tests 통과
- `bash -n scripts/verify_portfolio_remediation_ticket_report.sh`: 통과
- `bash scripts/verify_portfolio_remediation_ticket_report.sh`: 통과, Docker Postgres에서 BABA open ticket report 확인
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-ticket-report`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
