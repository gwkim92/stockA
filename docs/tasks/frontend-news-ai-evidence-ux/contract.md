# Task Contract

## Task

- 이름: frontend-news-ai-evidence-ux
- 요청: 뉴스 AI 후보 근거를 `/events`, `/intelligence`, `/ai-evidence/:id`에서 사람이 이해 가능한 흐름으로 보여준다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `news_event_candidate` artifact가 AI 근거 상세에서 뉴스 전용 구조로 표시되고, 이벤트 원장과 분석 지도에서 해당 AI 후보 근거 상세로 바로 이동할 수 있다.

## Why

- 현재 AI 근거 상세는 SEC extraction과 news cluster 중심이라 개별 뉴스 AI 후보의 테마/종목/방향/불확실성을 명확히 설명하지 못한다.
- 사용자는 어떤 뉴스가 어떻게 분석됐고 어떤 뉴스/종목/테마/추천에 연결됐는지 화면에서 추적해야 한다.
- 추천 품질 개선 전에 근거 추적 UX가 명확해야 한다.

## Scope

- 포함:
  - `AiEvidenceDetailData`에 뉴스 후보 구조화 payload 추가
  - event list DTO에 AI evidence type/provider/confidence metadata 추가
  - `/ai-evidence/[evidenceId]` 뉴스 후보 전용 UI
  - `/events` AI 후보 상태/링크 워딩 개선
  - `/intelligence` AI 후보 상태/링크 워딩 개선
  - focused tests and task docs
- 제외:
  - DB migration
  - recommendation scoring 공식 변경
  - new LLM invocation
  - broker/order flow
  - write API

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `docs/api/frontend/examples/event-list.json`
  - `docs/api/frontend/examples/ai-evidence-detail.json`
  - focused tests
  - `docs/tasks/frontend-news-ai-evidence-ux/`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - broker/order submission code
  - production credentials

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`
  - `bash scripts/verify_frontend_api_contract.sh`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-news-ai-evidence-ux`

## Done Criteria

- [x] `news_event_candidate` detail response keeps `evidence_type=news_event_candidate`.
- [x] AI evidence detail page has explicit news candidate section.
- [x] Event list shows AI evidence type/provider/confidence and links to candidate detail.
- [x] Intelligence trace labels news candidate evidence distinctly.
- [x] Focused verification commands pass.
