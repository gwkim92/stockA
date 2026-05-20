# Task Contract

## Task

- 이름: frontend-news-cluster-evidence-detail
- 요청: 저장된 `news_cluster_summary` AI evidence를 `/ai-evidence/...` 화면에서 사람이 이해할 수 있게 보여준다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/ai-evidence/{id}`가 `news_cluster_summary` artifact의 cluster summary와 구성 이벤트를 read-only DTO로 노출한다.
  - `/ai-evidence/{id}`는 뉴스 묶음 증거일 때 테마, 이벤트 수, 연결 종목, 영향 방향 분포, 대표 뉴스를 별도 섹션으로 보여준다.
  - 무료 로컬 규칙, 0 token, 0 cost 경계가 화면에서 이해 가능해야 한다.
  - 기존 source document evidence 화면은 깨지지 않아야 한다.

## Scope

- `ai.extraction_artifact.output_json.cluster`와 `output_json.events`를 기존 AI evidence detail API에 optional field로 추가한다.
- Next.js AI evidence detail 화면에 뉴스 묶음 전용 설명 섹션을 추가한다.
- 사용자에게 보이는 코드형 값은 한국어 라벨을 거쳐 표시한다.
- task handoff와 검증 증거를 남긴다.

## Boundaries

- DB schema, scoring, recommendation logic, broker/order flow는 변경하지 않는다.
- 새 write endpoint를 만들지 않는다.
- LLM, paid news provider, translation API를 호출하지 않는다.
- cluster summary는 투자 결론이 아니라 감사 가능한 검토 근거로 표시한다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/frontend-news-cluster-evidence-detail/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - authenticated FastAPI `/api/ai-evidence/ai-evidence-2` smoke confirms `cluster_summary` and `cluster_events`.
  - route smoke for `http://127.0.0.1:3001/ai-evidence/ai-evidence-2` confirms Korean news cluster copy.
  - Browser check for `/ai-evidence/ai-evidence-2`.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-news-cluster-evidence-detail`
  - `git diff --check`

## Done Criteria

- [x] AI evidence API exposes optional cluster summary/events for `news_cluster_summary`.
- [x] AI evidence page has a news-cluster-specific section.
- [x] Existing AI evidence response tests still pass.
- [x] Required verification passes.

## Verification Evidence

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - result: 33 tests passed.
- `cd apps/web && npm run build`
  - result: Next.js production build passed.
- `cd apps/web && npm run typecheck`
  - result: TypeScript check passed after build regenerated `.next/types`.
- Authenticated FastAPI smoke for `/api/ai-evidence/ai-evidence-2`
  - result: `news_cluster_summary`, provider `local_rules`, theme `AI_SEMICONDUCTOR_CYCLE`, 10 cluster events, symbols `["NVDA"]`.
- Browser check for `http://127.0.0.1:3001/ai-evidence/ai-evidence-2`
  - result: visible page contains `뉴스 묶음 증거`, `뉴스 묶음 분석`, `무료 로컬 규칙`, `대표 뉴스`, `원천 문서 열기`, `LLM 원천 청크 없음`; old `AI 증거 •` badge no longer appears.
