# Session Handoff

## Current Status

- 상태: completed
- completed: 뉴스/AI 흐름 화면의 사용자-facing 문구와 판단 경로를 정리했고 EC2 배포 검증까지 완료했다.
- 기준일: 2026-05-23

## Investigation

- `/intelligence`는 묶음 기준, 종목 관계, 추천 영향 함수를 이미 갖고 있으나 일부 copy가 `원장`, `검증기`, `LLM` 같은 내부 표현을 사용한다.
- `/events`는 제목과 설명이 `수집 뉴스 원장` 중심이라 사용자가 “이걸 왜 봐야 하는지”보다 원장 화면으로만 읽힌다.
- `/ai-evidence/[id]`는 상세 정보는 충분하지만 rejected/candidate/cluster 설명에 `validator`, `품질 관문`, `LLM` 같은 표현이 남아 있다.
- Playwright 확인 중 `/intelligence`에 `부분 준비 0/2`, `검색/RAG 확인용 문서 조각`처럼 사용자에게 의미가 불명확한 근거 검색 상태 문구가 추가로 발견되어 `원문 근거 연결`, `원문 근거 N개 연결`로 정리했다.

## Mutable Surface

- `apps/web/src/app/intelligence/page.tsx`
- `apps/web/src/app/events/page.tsx`
- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/news-ai-flow-clarity-pass/*`

## Verification Evidence

- local: `git diff --check` passed.
- local: `cd apps/web && npm run typecheck` passed.
- local: `cd apps/web && npm run build` passed.
- local: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-flow-clarity-pass` passed.
- EC2: `/opt/stockanalysis/app` reset to `1b11bf7`, `npm --prefix apps/web run build` passed, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active.
- EC2 route smoke: `/intelligence?refresh=1b11bf7`, `/events?refresh=1b11bf7`, `/ai-evidence/ai-evidence-248?refresh=1b11bf7` returned 200 with required user-facing text and without blocked internal terms.
- Playwright: `/intelligence?refresh=1b11bf7` snapshot confirmed the news flow, grouping basis, stock relation, and source evidence wording render correctly.

## Exact Next Step

- exact next step: 종목 상세와 추천 상세 화면에서 `뉴스 → 상위 흐름/직접 종목 → 점수/보유검토 → 가상 거래 상태`가 한 화면에서 추적되는지 점검하고, 사용자-facing 문구와 중복 섹션을 정리한다.
