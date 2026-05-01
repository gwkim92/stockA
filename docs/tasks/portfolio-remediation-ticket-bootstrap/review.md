# Review

## Review Notes

- `portfolio-remediation-ticket-bootstrap`은 queue item을 persistent ticket으로 저장한다.
- `portfolio.remediation_ticket` schema를 추가했다.
- 기존 portfolio review action rule, recommendation score, thesis generation, attribution, performance outcome calculation은 변경하지 않았다.
- `portfolio.review_item`은 review rerun 때 delete/insert되므로 ticket에는 `review_item_id` FK를 두지 않았다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_ticket tests.test_ingest_cli -v`: 통과
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 229 tests 통과
- `bash -n scripts/verify_portfolio_remediation_ticket_bootstrap.sh`: 통과
- `bash scripts/verify_portfolio_remediation_ticket_bootstrap.sh`: 통과, Docker Postgres에서 BABA ticket 생성과 duplicate 방지 확인
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-ticket-bootstrap`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
