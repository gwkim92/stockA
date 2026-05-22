# Session Handoff

## Current Status

- 상태: in_progress
- current status: in_progress
- 진행 중: AI 추출 필드와 투자 논리 제목의 raw code 표현을 사용자용 문구로 정리한다.
- 기준일: 2026-05-23

## Investigation

- `/ai-evidence/ai-evidence-136`의 추출 필드에 `QUANTUM_COMPUTING_POLICY / supportive / ...`, `chunk-news-ai-*` 값이 그대로 보인다.
- `/stocks/QUBT`와 `/ai-evidence/ai-evidence-136`의 투자 논리 카드에 `QUBT watch 투자 논리 via US Market Breadth`가 남아 있다.
- 이 문제는 DB 오염이라기보다 표시 계층에서 raw structured value를 그대로 보여준 결과다.

## Mutable Surface

- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/detail-code-value-wording-cleanup/*`

## Exact Next Step

- exact next step: AI 추출 필드 렌더러와 공통 label normalization을 수정한 뒤 로컬/EC2 화면에서 raw code 노출이 줄었는지 확인한다.
