# Review

## Verification

- Passed:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` - 52 tests OK
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_holding_thesis_bootstrap` - 7 tests OK
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation` - 6 tests OK
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_cluster_evidence` - 16 tests OK
  - `cd apps/web && npm run typecheck` - OK
  - `cd apps/web && npm run build` - OK
  - `git diff --check` - OK
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task ai-autonomous-review-boundary` - passed readiness checks

## Risks

- DB/schema와 일부 API field 이름에는 legacy `human_*` key가 남아 있다. 이번 작업은 schema rename이 아니라 사용자 화면/read model 표현과 품질 상태 전환이다.
- 실거래/브로커 주문 자동 승인은 여전히 범위 밖이다. AI 검토가 통과해도 거래 안전 경계, 주문 한도, kill switch는 유지한다.
- `apps/web/src/lib/korean-labels.ts`에는 과거 DB 값과 과거 audit note를 한국어로 바꾸기 위한 legacy English key가 남아 있다. 신규 화면 문구는 AI 검토 표현으로 매핑된다.
