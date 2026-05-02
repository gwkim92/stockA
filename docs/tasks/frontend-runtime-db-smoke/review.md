# Review

## Review Notes

- `scripts/verify_frontend_runtime_db_smoke.sh`는 disposable Docker Postgres에 migrations/seeds를 적용하고 deterministic fixture pipeline을 실행한다.
- smoke는 `source=live`, `runtime_profile=production`, explicit CORS, `read-token` auth로 HTTP runtime을 시작한다.
- `/__health` public, `/api/dashboard/today` unauthorized rejection, authorized live DTO reads를 검증한다.
- schema, benchmark, scoring, write API, connection pooling, full auth/RBAC는 변경하지 않았다.

## Verification Evidence

- `bash scripts/verify_frontend_runtime_db_smoke.sh`: 통과.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-runtime-db-smoke`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 284 tests.
- `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
