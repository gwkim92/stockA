# Review

## Review Notes

- `portfolio-remediation-queue`는 `portfolio.review_item`에서 조치 필요 action만 읽는 read-only report다.
- DB migration, portfolio review rule, attribution, recommendation score, thesis generation rule은 변경하지 않았다.
- 현재 queue는 상태를 저장하지 않으므로 repeated item 추적과 담당자/마감일 관리는 아직 없다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_queue tests.test_ingest_cli -v`: 통과
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 225 tests 통과
- `bash -n scripts/verify_portfolio_remediation_queue_report.sh`: 통과
- `bash scripts/verify_portfolio_remediation_queue_report.sh`: 통과, Docker Postgres에서 BABA `needs_thesis_review` -> `thesis_remediation` 확인
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-queue-report`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
