# codex-oauth-news-smoke-cli-boundary-v1 Contract

## Task Request

- request: Codex OAuth 운영 콘솔의 `뉴스 AI 확인`이 EC2 FastAPI systemd PATH 문제로 실패하지 않게 한다.
- context: 직접 Codex OAuth smoke는 성공했지만 뉴스 smoke는 `[Errno 2] No such file or directory: 'stockanalysis-operations'`로 실패했다. 이는 OAuth 인증 문제가 아니라 FastAPI 서비스 프로세스가 operations CLI binary를 PATH에서 찾지 못하는 배포 경계 문제다.

## Goal

- goal: `run_codex_oauth_news_smoke`가 systemd PATH에 의존하지 않고 현재 Python interpreter로 `stockanalysis.operations.cli`를 실행해 뉴스 번역/구조화 smoke를 수행한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/codex_oauth_operator.py`
  - `tests/test_codex_oauth_operator.py`
  - `docs/tasks/codex-oauth-news-smoke-cli-boundary-v1/*`

## Invariants

- 추천 weight 변경 금지
- broker/order flow 변경 금지
- scheduler cadence 변경 금지
- OpenAI API billing 정책 변경 금지
- Codex OAuth 토큰 파일 내용 노출 금지

## Non-Goals

- 추천 weight 변경 금지
- broker/order flow 변경 금지
- scheduler cadence 변경 금지
- OpenAI API billing 정책 변경 금지

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task codex-oauth-news-smoke-cli-boundary-v1`
- verification command: `EC2 POST /__admin/codex-oauth/smoke/news`

## Done Criteria

- 뉴스 smoke가 기본적으로 `sys.executable -m stockanalysis.operations.cli ...`를 사용한다.
- 필요하면 `STOCKANALYSIS_OPERATIONS_COMMAND`로 command override가 가능하다.
- unit test가 CLI boundary를 고정한다.
- EC2에서 직접 smoke와 뉴스 smoke가 모두 성공한다.
