# recommendation-detail-decision-waterfall-v3 Contract

## Task Request

- request: 추천 상세 화면에서 거시→테마→기업→재무→밸류에이션→리스크→페이퍼 검증 순서가 첫 화면에서 선명하게 보이도록 재구성한다.

## Goal

- goal: `/recommendations/{id}` 첫 화면에서 이 추천의 현재 판정, 주문 경계, 핵심 근거 축, 다음 확인 위치를 한눈에 볼 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/recommendation-detail-decision-waterfall-v3/*`

## Invariants

- 추천 scoring formula, recommendation weights, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.
- 화면은 저장된 read-only 데이터만 조합하며 실시간 AI 호출이나 주문 생성을 하지 않는다.

## Scope

- 추천 상세 hero 직후 `추천 결론` waterfall 패널을 추가한다.
- 거시, 테마, 기업, 재무, 밸류에이션, 리스크, 페이퍼 검증 단계를 분리해 보여준다.
- 각 단계에서 관련 상세 섹션으로 이동할 수 있는 앵커/링크를 제공한다.
- 기존 전문 의사결정 흐름, 기업 리서치, 사이클, 근거 검토 섹션에 읽는 순서를 드러내는 id와 제목 문구를 보강한다.
- 모바일에서 waterfall이 1열로 내려오도록 CSS를 추가한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-decision-waterfall-v3`
- verification command: `git diff --check`
- verification command: EC2/local tunnel route smoke for `/recommendations/recommendation-157`

## Done Criteria

- [x] `/recommendations/recommendation-157`에 `추천 결론` 패널이 렌더링된다.
- [x] waterfall 단계 `거시`, `테마`, `기업`, `재무`, `밸류에이션`, `리스크`, `페이퍼 검증`이 보인다.
- [x] 주문 차단/읽기 전용 경계가 첫 화면에서 보인다.
- [x] 단계별 상세 이동 링크가 보인다.
- [ ] local verification과 EC2 route smoke가 통과한다.
