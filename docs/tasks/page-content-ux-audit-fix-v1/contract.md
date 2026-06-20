# page-content-ux-audit-fix-v1 Contract

## Task Request

- request: 현재 존재하는 주요 화면의 문구, 콘텐츠, UX/UI, 데이터 분석 상태를 점검하고 즉시 수정 가능한 가시성 문제를 고친다.

## Goal

- goal: `/`는 반복 보완 CTA를 상위 5개 묶음으로 압축하고, `/data-health`는 뉴스 AI 평가 case와 주요 실행 이력을 한국어 라벨로 표시하여 사용자가 오늘 확인할 항목을 바로 이해할 수 있게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/page-content-ux-audit-fix-v1/*`

## Invariants

- Do not change DB schema.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions.
- Do not change portfolio positions.
- Do not change broker/order flow or live trading.

## Scope

- 포함:
  - 주요 Next.js route 목록 확인
  - 홈 우선순위 보완 항목 과다 반복 축소
  - AI 평가 case와 주요 runner/status 코드 한국어 라벨 보강
  - 브라우저/route smoke 기반 표시 검증
- 제외:
  - DB schema 변경
  - 추천 scoring weight 변경
  - benchmark 정의 변경
  - portfolio position 변경
  - broker/order flow 변경
  - 실거래 활성화

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task page-content-ux-audit-fix-v1`
- verification command: route smoke for `/`, `/data-health`, `/intelligence`, `/ai-evidence`, `/cycle-map`, `/recommendations`, `/stocks`, `/paper-trading`

## Done Criteria

- [x] 홈에서 동일한 `보완 큐에서 처리` CTA가 수십 번 반복되지 않는다.
- [x] `/data-health`의 뉴스 AI 평가 case가 한국어로 표시된다.
- [x] 주요 runner/status 코드가 사용자용 한국어 문구로 표시된다.
- [x] 검증 명령과 route smoke가 통과한다.
