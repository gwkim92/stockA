# codex-oauth-force-relogin-code-v1 Contract

## Task Request

- request: `/admin/ai-agents`에서 `새 로그인 코드 받기`를 눌러도 새 코드가 화면에 보이지 않는 문제를 고친다.
- context: 버튼 클릭은 Next server action을 실행하지만 EC2 응답은 기존 `healthy` 상태를 그대로 반환해 `user_code`가 빈 값으로 남는다.

## Goal

- goal: 사용자가 `새 로그인 코드 받기`를 누르면 기존 Codex OAuth 상태가 healthy여도 새 device login code가 발급되고 화면에 표시된다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/codex_oauth_operator.py`
  - `tests/test_codex_oauth_operator.py`
  - `docs/tasks/codex-oauth-force-relogin-code-v1/*`

## Non Goals

- OpenAI/Codex OAuth 계정 자체의 인증을 대신 완료하지 않는다.
- 추천 weight, broker/order flow, scheduler cadence는 변경하지 않는다.
- admin action token 경계는 완화하지 않는다.

## Acceptance Criteria

- `start_codex_oauth_device_login()`은 기존 상태가 `healthy` 또는 `authenticated_smoke_required`여도 명시적 relogin 요청이면 새 code를 발급한다.
- 기존 pending code가 있을 때도 새 code로 교체된다.
- 화면에서 새 code와 인증 URL이 보인다.
- 관리자 action token 요구는 유지된다.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_codex_oauth_operator -v`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_server.FrontendApiServerTests.test_codex_oauth_admin_action_allows_explicit_operator_token -v`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task codex-oauth-force-relogin-code-v1`
