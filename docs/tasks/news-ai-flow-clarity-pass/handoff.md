# Session Handoff

## Current Status

- 상태: in_progress
- in progress: 뉴스/AI 흐름 화면의 사용자-facing 문구와 판단 경로를 정리 중이다.
- 기준일: 2026-05-23

## Investigation

- `/intelligence`는 묶음 기준, 종목 관계, 추천 영향 함수를 이미 갖고 있으나 일부 copy가 `원장`, `검증기`, `LLM` 같은 내부 표현을 사용한다.
- `/events`는 제목과 설명이 `수집 뉴스 원장` 중심이라 사용자가 “이걸 왜 봐야 하는지”보다 원장 화면으로만 읽힌다.
- `/ai-evidence/[id]`는 상세 정보는 충분하지만 rejected/candidate/cluster 설명에 `validator`, `품질 관문`, `LLM` 같은 표현이 남아 있다.

## Mutable Surface

- `apps/web/src/app/intelligence/page.tsx`
- `apps/web/src/app/events/page.tsx`
- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `docs/tasks/news-ai-flow-clarity-pass/*`

## Exact Next Step

- exact next step: 세 화면의 사용자-facing 문구에서 내부 용어를 제거하고, 묶음 기준/종목 연결/추천 입력 상태를 명확히 설명한 뒤 typecheck/build/AWH와 EC2 route smoke를 실행한다.
