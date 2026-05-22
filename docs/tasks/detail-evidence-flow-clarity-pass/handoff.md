# Session Handoff

## Current Status

- 상태: completed
- current status: completed
- 완료: 상세 페이지 3곳의 읽는 순서와 사용자용 근거 문구를 보강했다.
- 기준일: 2026-05-23

## Goal

- 종목 상세, 추천 상세, AI 근거 상세에서 뉴스 -> 상위 흐름 -> 종목 -> 추천 점수 경로를 사용자 문장으로 정리한다.
- API/DB/추천 산식은 변경하지 않는다.

## Investigation

- `/stocks/[symbol]`에는 관계망이 있으나 `retrieval_backend`, `token budget`, `문서 청크`, `임베딩` 같은 내부 용어가 전면에 노출된다.
- `/recommendations/[recommendationId]`에는 evidence trace가 있으나 `macro_flow_score`, `preview`, `provenance` 같은 구현 용어가 설명문에 남아 있다.
- `/ai-evidence/[evidenceId]`는 검증 구조가 있으나 “AI가 무엇을 했고 어디까지 추천 입력인지”를 상단에서 더 짧게 보여줄 필요가 있다.

## Implemented

- `/stocks/[symbol]` 상단에 `먼저 볼 것`, `직접 뉴스`, `상위 흐름`, `최종 확인` 읽는 순서 카드를 추가했다.
- `/stocks/[symbol]`의 관계망 배지와 근거 문서 문구에서 `retrieval`, token, raw storage 문구를 제거했다.
- `/stocks/[symbol]`의 상위 흐름 전파 rationale은 raw AI/DB 문자열 대신 화면용 요약 문장으로 표시한다.
- `/recommendations/[recommendationId]` 상단에 `결론`, `가격/순위`, `뉴스/AI`, `상위 흐름` 점수 재료 카드를 추가했다.
- `/recommendations/[recommendationId]`의 `macro_flow_score`, `preview`, `provenance` 전면 문구를 사용자 문장으로 바꿨다.
- `/ai-evidence/[evidenceId]` 상단에 `AI가 한 일`, `연결 대상`, `추천 사용`, `다음 확인` 읽는 순서 카드를 추가했다.
- `/ai-evidence/[evidenceId]`의 source chunk/raw retrieval context 표시는 제목, 요약, 발행 시각, 출처 요약으로 바꿨다.

## Verification Log

- PASS: local `cd apps/web && npm run typecheck`
- PASS: local `cd apps/web && npm run build`
- PASS: local `git diff --check`
- PASS: local `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task detail-evidence-flow-clarity-pass`
- PASS: EC2 deploy to commit `bca50dd`
- PASS: EC2 `npm --prefix apps/web run typecheck`
- PASS: EC2 `npm --prefix apps/web run build`
- PASS: EC2 `stockanalysis-frontend-api.service` active and `stockanalysis-web.service` active
- PASS: EC2 route smoke returned HTTP `200` for `/stocks/QUBT`, `/recommendations/recommendation-52`, `/ai-evidence/ai-evidence-136`
- PASS: rendered HTML contains detail reading-order text for stock, recommendation, and AI evidence detail pages.
- PASS: Playwright snapshot verified `/stocks/QUBT`, `/recommendations/recommendation-52`, `/ai-evidence/ai-evidence-136` through the EC2 tunnel at `http://127.0.0.1:13000`.

## Remaining

- 일부 AI 추출 필드 값 자체에는 `QUANTUM_COMPUTING_POLICY`, `supportive`, `chunk-news-ai-*` 같은 원본 구조화 값이 남아 있다. 다음 slice에서 field value 렌더러를 별도로 정리한다.
- `QUBT` 투자 논리 제목에 `via US Market Breadth`가 남아 있다. thesis 생성/표시 문구 정리에서 보정한다.
- 일부 추천 상세의 상위 흐름 사례에는 broad market 뉴스가 섞인다. 다음 taxonomy hardening에서 남은 오분류를 계속 줄인다.

## Mutable Surface

- `apps/web/src/app/stocks/[symbol]/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/detail-evidence-flow-clarity-pass/*`

## Exact Next Step

- exact next step: AI 추출 필드 값 렌더러와 thesis/recommendation 제목의 남은 내부 코드 표현을 정리한다.
