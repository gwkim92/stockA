# Task Contract

## Task Request

- request: Codex OAuth가 실패해도 fallback과 fixture 평가에 묻히지 않도록 실제 LLM 호출 상태를 `/data-health`에서 강하게 노출한다.

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/data-health`가 최근 실제 `ai.model_invocation` 기반 `live_ai_invocation_health`를 반환한다.
  - 최근 Codex OAuth 번역/뉴스 구조화가 실패하면 `open_gates`에 `live_ai_invocation_health_attention`이 추가된다.
  - `/data-health`가 fixture 회귀평가와 실제 LLM 호출 상태를 분리해서 보여준다.

## Scope

- 포함:
  - data-health SQL에 최근 Codex OAuth task별 성공/실패 집계 추가
  - live adapter payload와 open gate detail 추가
  - Next 타입과 `/data-health` 한국어 UI 추가
  - 테스트와 handoff 갱신
- 제외:
  - DB schema migration
  - scheduler timer/unit 변경
  - 추천 scoring weight 변경
  - broker/order flow
  - 유료 외부 RAG/그래프 도구 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/live-ai-invocation-health-gate-v1/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - systemd scheduler unit/timer files
  - broker/order submission code

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task live-ai-invocation-health-gate-v1`
- verification command: EC2 `/api/data-health` and `/data-health` smoke

## Done Criteria

- [ ] 실제 Codex OAuth 실패가 `/api/data-health.open_gates`에 표시된다.
- [ ] `/data-health`가 “회귀평가 통과”와 “실제 LLM 실패”를 혼동하지 않게 보여준다.
- [ ] 검증 결과와 남은 위험이 handoff에 기록된다.
