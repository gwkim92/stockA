# Review

## Review Notes

- `docs/frontend-api-contract.md`가 common response shape, endpoint table, DTO ownership, read/write boundary를 정의한다.
- `docs/api/frontend/contract-index.json`이 seven read endpoints와 example payload를 연결한다.
- seven examples는 daily cockpit, remediation tickets, data health, cycle state list, recommendation detail, thesis detail, portfolio coverage를 포함한다.
- actual API server나 frontend scaffold는 생성하지 않았다.

## Verification Evidence

- `bash -n scripts/verify_frontend_api_contract.sh`: 통과
- `bash scripts/verify_frontend_api_contract.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-contract-foundation`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
