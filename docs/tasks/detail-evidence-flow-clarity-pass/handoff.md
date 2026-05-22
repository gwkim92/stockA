# Session Handoff

## Current Status

- 상태: in_progress
- current status: in_progress
- 진행 중: 상세 페이지 3곳의 읽는 순서와 사용자용 근거 문구를 보강한다.
- 기준일: 2026-05-23

## Goal

- 종목 상세, 추천 상세, AI 근거 상세에서 뉴스 -> 상위 흐름 -> 종목 -> 추천 점수 경로를 사용자 문장으로 정리한다.
- API/DB/추천 산식은 변경하지 않는다.

## Investigation

- `/stocks/[symbol]`에는 관계망이 있으나 `retrieval_backend`, `token budget`, `문서 청크`, `임베딩` 같은 내부 용어가 전면에 노출된다.
- `/recommendations/[recommendationId]`에는 evidence trace가 있으나 `macro_flow_score`, `preview`, `provenance` 같은 구현 용어가 설명문에 남아 있다.
- `/ai-evidence/[evidenceId]`는 검증 구조가 있으나 “AI가 무엇을 했고 어디까지 추천 입력인지”를 상단에서 더 짧게 보여줄 필요가 있다.

## Mutable Surface

- `apps/web/src/app/stocks/[symbol]/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/detail-evidence-flow-clarity-pass/*`

## Exact Next Step

- exact next step: 상세 페이지 3곳의 상단 읽는 순서와 내부 용어 문구를 정리하고, 로컬/EC2 검증 결과를 이 파일에 기록한다.
