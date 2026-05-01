# Review

## Review Notes

- `portfolio-remediation-ticket-update`는 persistent ticket status만 변경하는 lifecycle command다.
- DB schema, review action rule, recommendation score, thesis generation, attribution, performance outcome calculation은 변경하지 않았다.
- `source_run_id`는 bootstrap provenance로 유지하고, update 실행은 별도 `ops.pipeline_run`으로 남긴다.
- sandbox 내부 Docker 실행은 daemon socket 권한 때문에 실패했고, 승인된 외부 실행으로 같은 검증을 통과했다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_ticket tests.test_ingest_cli -v`: 통과
- `bash -n scripts/verify_portfolio_remediation_ticket_update.sh`: 통과
- `bash scripts/verify_portfolio_remediation_ticket_update.sh`: 승인된 외부 실행으로 통과, Docker Postgres에서 BABA ticket resolved lifecycle 확인
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 239 tests 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-ticket-update`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
