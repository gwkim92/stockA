# Session Handoff

## Current Status

- 상태: completed
- completed: 종목 상세, 추천 상세, 가상 거래 화면의 판단 흐름과 사용자-facing 문구를 정리하고 EC2 배포 검증까지 완료했다.
- 기준일: 2026-05-23

## Investigation

- `/stocks/[symbol]`는 가격 차트, 추천, 보유, 뉴스, 상위 흐름을 모두 갖고 있으나 일부 링크/문구가 `이벤트 원장`, `검색 준비 상태`, `근거 문서 조각`처럼 내부 표현이다.
- `/recommendations/[id]`는 직접 뉴스, 상위 흐름, 보유검토 trace가 있으나 링크 라벨이 `이벤트 원장 열기`, `종목 흐름 보기` 등으로 흐름을 충분히 설명하지 못한다.
- `/paper-trading`은 실제 주문 여부와 가상 후보 상태를 보여주지만, 첫 화면에서 “현재 할 수 있는 것/할 수 없는 것/다음 확인 화면”이 더 명확해야 한다.
- Playwright 검증 중 `/stocks/QUBT`에 `임베딩 미생성`, `근거 문서`가 visible text로 남아 있어 `원문 저장됨`, `원문 근거`로 추가 정리했다.
- `/recommendations/recommendation-75`에는 백엔드가 넘긴 `읽기 전용 품질 점검` 설명이 visible text로 남아 있어 한국어 라벨 계층에서 `읽기 전용 근거 점검`으로 치환했다.

## Mutable Surface

- `apps/web/src/app/stocks/[symbol]/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/paper-trading/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/decision-detail-flow-clarity-pass/*`

## Verification Evidence

- local: `git diff --check` passed.
- local: `cd apps/web && npm run typecheck` passed after rerunning separately from build. A concurrent run with `next build` produced a transient `.next/types/routes.js` timing error, so typecheck was rerun alone and passed.
- local: `cd apps/web && npm run build` passed.
- local: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-detail-flow-clarity-pass` passed before route smoke.
- EC2: `/opt/stockanalysis/app` reset to `cd33442`, `npm --prefix apps/web run build` passed, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active.
- EC2 route smoke: `/stocks/QUBT?refresh=cd33442`, `/recommendations/recommendation-75?refresh=cd33442`, `/paper-trading?refresh=cd33442` returned 200 with required user-facing text and without blocked internal terms.
- Playwright: snapshots captured for `/stocks/QUBT`, `/recommendations/recommendation-75`, and `/paper-trading`; snapshot text checks passed.

## Exact Next Step

- exact next step: `/data-health`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/trading-readiness`를 한 번 더 연결해 운영 상태와 AI 분석 상태가 사용자용 모니터링 화면으로 보이는지 점검한다.
