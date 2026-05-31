# recommendation-thesis-detail-decision-ux-v1

## Task Request

- request: 사용자가 진행 중인 전체 UX/UI 리팩터링 흐름에서 추천 상세와 투자 논리 상세를 다음 점검 대상으로 계속 진행하라고 요청했다.

## Goal

- goal: 추천 상세와 연결된 투자 논리 상세 화면을 사용자가 바로 읽을 수 있는 투자 판단 흐름으로 정리한다.

핵심 질문은 아래 세 가지다.

- 이 추천은 현재 채택, 보류, 차단 중 어디에 가까운가?
- 근거는 거시, 테마, 기업, 재무, 밸류에이션, 리스크, 페이퍼 검증 중 어디까지 연결됐는가?
- 증권사 주문, 추천 산식 가중치 변경, 페이퍼 검증 입력은 각각 허용인지 차단인지?

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/recommendation-thesis-detail-decision-ux-v1/*`

## Non-Goals

- 추천 score component weight 변경 금지
- benchmark, portfolio position, paper order, broker submit 변경 금지
- API DTO, DB schema, scheduler cadence 변경 금지
- 새로운 AI 호출 또는 데이터 수집 로직 추가 금지

## Acceptance Criteria

- 추천 상세 첫 화면에서 `페이퍼 검증`과 `증권사 주문` 상태가 분리되어 보인다.
- 사용자 화면의 `thesis`, `artifact`, `gate`, `weight` 같은 내부 용어가 필요한 곳을 제외하고 한국어 사용자 문장으로 바뀐다.
- 투자 논리 상세 화면에서 `전문 Thesis Gate` 같은 혼합 표현이 사라진다.
- 검증은 Next typecheck/build, AWH task verify, EC2 route smoke로 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-thesis-detail-decision-ux-v1`
- verification command: EC2 route smoke for `/recommendations/<id>` and `/theses/<id>`
