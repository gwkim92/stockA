# intelligence-flow-clarity-v1 Contract

## Task Request

- request: Continue the UX wording cleanup on `/intelligence`.
- context: The source-news and AI evidence route groups were clarified, but `/intelligence` still mixes older wording such as `뉴스·AI 판단`, `AI 후보`, `뉴스 묶음 증거`, `보유 검토`, and `페이퍼` with the newer evidence journey language.

## Goal

- goal: Make `/intelligence` read as the high-level decision map for news flow:

`오늘의 상위 흐름 → 통과한 AI 근거 → 차단/오염 의심 → 추천 상세·보유 상태·가상 매매 연결`

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/intelligence/page.tsx`
  - `docs/tasks/intelligence-flow-clarity-v1/*`

## Invariants

- Do not change API DTO contracts.
- Do not change scheduler cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, automatic rebalancing, or write APIs.

## Scope

- Replace system wording around `AI 후보` with `AI 구조화 항목` or `AI 근거`.
- Replace `뉴스·AI 판단` with `뉴스 흐름과 AI 근거`.
- Replace `뉴스 묶음 증거` with `뉴스 묶음 근거`.
- Replace `보유 검토`/`보유검토` with `보유 상태 판단`.
- Replace user-facing `페이퍼` shorthand with `가상 매매`.
- Preserve source-news Korean translations as source content.

## Verification

- verification command: `rg -n "AI 후보|뉴스·AI 판단|뉴스 묶음 증거|AI 증거|보유검토|보유 검토|페이퍼|검토서" apps/web/src/app/intelligence/page.tsx`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: route smoke for `/intelligence`.
- verification command: browser text smoke for `/intelligence`.
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task intelligence-flow-clarity-v1`
