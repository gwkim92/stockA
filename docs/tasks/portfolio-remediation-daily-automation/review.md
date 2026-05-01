# Review

## Review Notes

- `portfolio-remediation-daily-run`은 기존 deterministic runner를 조합한다.
- 실행 순서는 portfolio review bootstrap, remediation ticket bootstrap, remediation ticket report다.
- top-level pipeline run은 `portfolio_remediation_daily_automation`으로 남긴다.
- 실제 scheduler를 활성화하지 않는다.
- ticket status update, remediation 실행, 실거래 주문/체결은 자동화하지 않는다.
- sandbox 내부 Docker 실행은 daemon socket 권한 때문에 실패했고, 승인된 외부 실행으로 같은 검증을 통과했다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_daily -v`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_daily tests.test_ingest_cli -v`: 43 tests 통과
- `bash -n scripts/verify_portfolio_remediation_daily_automation.sh`: 통과
- `bash scripts/verify_portfolio_remediation_daily_automation.sh`: 승인된 외부 실행으로 통과, Docker Postgres에서 daily runner와 BABA open ticket 확인
- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 243 tests 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-remediation-daily-automation`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: placeholder 없음
