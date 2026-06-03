# ai-evidence-review-journey-clarity-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on the AI evidence route group.
- context: Source/news routes were clarified, but `/ai-evidence`, `/ai-evidence/[evidenceId]`, and `/ai-evidence/blocked` still exposed ambiguous wording such as `AI 후보`, `검토서`, `보유검토`, `AI 판단`, and `AI 증거`.

## Goal

- goal: Make the AI evidence page group understandable as an evidence journey:

`원천 뉴스 → 한국어 번역 → AI 구조화 항목 → 자동 검증 통과/차단 → 추천 상세/종목 상세 연결`

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/components/news-event-card.tsx`
  - `docs/tasks/ai-evidence-review-journey-clarity-v1/*`

## Scope

- `/ai-evidence`
- `/ai-evidence/[evidenceId]`
- `/ai-evidence/blocked`
- Shared wording only where these pages render it.

## Non-Goals

- No API contract changes.
- No schema changes.
- No recommendation scoring weight changes.
- No benchmark, portfolio position, broker, or order-flow changes.
- No new shell orchestration for data operations.

## Decisions

- Use `AI 구조화 항목`, `AI 근거`, `자동 검증`, `차단 항목`, `보유 상태 판단`, and `추천 상세` consistently.
- Avoid implying a human review workflow when there is no review action UI.
- Avoid `AI 후보`, `검토서`, `보유검토`, `AI 판단`, and `AI 증거` in user-facing copy.
- Preserve read-only/order-boundary language: AI evidence can support recommendation inputs, but never creates orders.

## Acceptance Criteria

- Target pages no longer expose old ambiguous terms:
  - `AI 후보`
  - `검토서`
  - `보유검토`
  - `AI 판단`
  - `AI 증거`
  - `뉴스 묶음 증거`
- Target pages clearly separate:
  - directly linked stock news
  - macro/theme flow news
  - validator-blocked or low-signal items
  - recommendation and stock detail links
- Typecheck, build, AWH verify, EC2 route smoke, and browser text smoke pass.

## Verification

- verification command: `rg -n "AI 후보|검토서|보유검토|AI 판단|AI 증거|뉴스 묶음 증거|AI 추출 증거|후보" apps/web/src/app/ai-evidence apps/web/src/components/news-event-card.tsx`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/ai-evidence`, `/ai-evidence/[evidenceId]`, `/ai-evidence/blocked`, and `/ai-evidence/results`.
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-review-journey-clarity-v1`
