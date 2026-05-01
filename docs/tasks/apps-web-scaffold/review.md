# Review Notes

## Scope Review

- 작업 범위는 fixture-only `apps/web` scaffold로 제한한다.
- live DB read adapter, auth/RBAC, write APIs, production deployment, broker integration은 범위 밖이다.

## Verification Evidence

- `npm install --no-audit --fund=false --verbose`: 통과
- `bash scripts/verify_apps_web_scaffold.sh`: 통과
- `npm run typecheck`: `verify_apps_web_scaffold.sh` 안에서 통과
- `next build`: `verify_apps_web_scaffold.sh` 안에서 통과
- fixture server runtime smoke: `verify_apps_web_scaffold.sh` 안에서 통과
- Next production route smoke for `/`, `/remediation`, `/data-health`, `/cycles`: `verify_apps_web_scaffold.sh` 안에서 통과
- frontend architecture/API/adapter/fixture server regression checks: `verify_apps_web_scaffold.sh` 안에서 통과
- `bash scripts/verify_frontend_fixture_server.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task apps-web-scaffold`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Residual Risks

- fixture server가 실행 중이어야 runtime page fetch가 성공한다.
- UI는 fixture examples 기반이라 live data freshness를 증명하지 않는다.
- 첫 scaffold는 in-app browser visual QA와 accessibility audit 전의 최소 shell이다.
