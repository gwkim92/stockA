# Task Contract

## Task

- 이름: ai-evidence-story-groups
- 요청: 종목별 AI 증거 관계망에서 뉴스가 어떤 이야기로 묶이고 왜 연결됐는지 사람이 이해할 수 있게 보여준다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/ai/evidence-neighborhoods/{symbol}` 응답에 deterministic `story_groups`가 포함된다.
  - 각 story group은 대표 제목, 연결 이벤트, 원천 문서, 관련 chunk, 테마, 연결 이유, 로컬 휴리스틱 신뢰도를 포함한다.
  - `/stocks/{symbol}` 화면은 “뉴스 이야기 묶음”을 한국어로 보여주고 왜 묶였는지 설명한다.
  - 이 기능은 read-only이며 추천 점수, thesis, 주문, scheduler, DB schema를 바꾸지 않는다.

## Scope

- 포함:
  - frontend live adapter DTO post-processing
  - deterministic title/source/theme based story grouping
  - TypeScript contract update
  - stock detail UI explanation panel
  - targeted tests and browser check
- 제외:
  - paid LLM call
  - vector DB or external embedding provider
  - DB migration
  - recommendation score generation
  - paper/live broker write flow
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `docs/plans/2026-05-20-ai-evidence-story-groups.md`
  - `docs/tasks/ai-evidence-story-groups/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-evidence-story-groups`
  - `git diff --check`

## Done Criteria

- [x] API story group payload is present and tested.
- [x] Stock detail page renders story groups with readable Korean wording.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
