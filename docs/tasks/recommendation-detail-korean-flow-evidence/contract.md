# Task Contract

## Task

- 이름: recommendation-detail-korean-flow-evidence
- 요청: 추천 상세에서 직접 뉴스와 상위 흐름 전파 근거가 영어 제목 중심으로 보이면 한국 사용자가 추천 근거를 바로 검토하기 어렵다. 저장된 한국어 번역 필드를 추천 상세 DTO와 화면에 연결한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/recommendations/[id]`에서 직접 뉴스/AI 근거와 상위 흐름 전파 근거가 `korean_title`, `korean_summary`, `translation_confidence`를 사용해 한국어로 먼저 보이고, 영어 원문은 접어서 확인할 수 있다.

## Scope

- 포함:
  - recommendation detail live SQL에 직접 뉴스와 macro flow source document 번역 필드 추가
  - recommendation detail DTO builder에 번역 필드 추가
  - Next.js 추천 상세 화면에서 `NewsTitleBlock`에 번역 필드 전달
  - focused live adapter test 갱신
- 제외:
  - 새 번역 실행 또는 AI 호출
  - 추천 점수 산식 변경
  - DB schema 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/recommendation-detail-korean-flow-evidence/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring formulas
  - scheduler configuration

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-detail-korean-flow-evidence`
  - EC2 deploy 후 recommendation detail route smoke

## Done Criteria

- [x] Recommendation detail API returns Korean translation fields for direct evidence and macro flow recent flows.
- [x] Recommendation detail page passes Korean translation fields into `NewsTitleBlock`.
- [x] Focused local verification passes.
- [ ] EC2 route smoke passes.
