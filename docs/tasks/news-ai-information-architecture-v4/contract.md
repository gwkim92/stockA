# news-ai-information-architecture-v4 Contract

## Task Request

- request: 뉴스·AI 화면이 한 화면에 원장, 후보, 구조화 결과를 과하게 섞어 보여주므로 대표 흐름 중심으로 줄이고, AI 근거 상세에서 한국어 번역이 있는 원천을 우선 보여준다.

## Goal

- goal: `/intelligence`를 “오늘 먼저 볼 대표 뉴스 흐름” 허브로 만들고, 전체 원장·AI 후보·통과/차단 결과는 전용 화면으로 분리해 연결한다. `/ai-evidence/[evidenceId]`는 묶음 첫 뉴스에 번역이 없어도 묶음 안의 한국어 번역된 대표 뉴스를 우선 사용한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `docs/tasks/news-ai-information-architecture-v4/*`

## Invariants

- Do not change backend DTO shape.
- Do not change DB schema or data operations jobs.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not hide warnings, blockers, source limits, or read-only order boundaries.

## Scope

- Reduce the number of news clusters shown by default.
- Reduce the number of AI candidate events shown by default.
- Add clear links to source news ledger, AI candidate list, structured result list, and blocked candidate list.
- Prefer translated cluster events for AI evidence source preview.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-information-architecture-v4`

## Done Criteria

- [x] `/intelligence` defaults to representative news flow rather than full mixed lists.
- [x] Full news/source/AI lists remain reachable through explicit CTAs.
- [x] AI evidence detail uses a translated cluster/evidence preview when available.
- [x] Local frontend verification passes.
- [x] EC2 and local tunnel route smoke pass.
