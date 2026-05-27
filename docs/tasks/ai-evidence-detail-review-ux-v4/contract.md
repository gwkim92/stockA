# ai-evidence-detail-review-ux-v4 Contract

## Task Request

- request: AI 근거 상세 화면에서 원천 뉴스 번역, AI 구조화 결과, validator 통과/차단, 종목·추천 연결을 더 짧은 판단 순서로 재구성한다.

## Goal

- goal: `/ai-evidence/{id}` 첫 화면에서 이 근거를 추천 입력으로 믿어도 되는지, 무엇을 먼저 확인해야 하는지, 어디로 이동해야 하는지 한눈에 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-evidence-detail-review-ux-v4/*`

## Invariants

- 추천 scoring formula, recommendation weights, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.
- 화면은 저장된 read-only 데이터만 조합하며 실시간 AI 호출이나 주문 생성을 하지 않는다.

## Scope

- AI 근거 상세 hero 직후 `AI 근거 결론` 패널을 추가한다.
- `원천·번역`, `AI 구조화`, `자동 검증`, `종목·추천 연결` 4단계 판단 카드를 제공한다.
- 기존 원천/구조화/검증/연결 상세 섹션으로 이동하는 앵커를 추가한다.
- 기존 5단계 trace와 visibility trace의 중복 체감을 줄이고, 상세 근거는 보조 섹션으로 남긴다.
- 모바일에서 결론 패널이 1열로 내려오도록 CSS를 추가한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-detail-review-ux-v4`
- verification command: `git diff --check`
- verification command: EC2/local tunnel route smoke for `/ai-evidence/ai-evidence-251`

## Done Criteria

- [x] `/ai-evidence/ai-evidence-251`에 `AI 근거 결론` 패널이 렌더링된다.
- [x] 4단계 `원천·번역`, `AI 구조화`, `자동 검증`, `종목·추천 연결`이 보인다.
- [x] 원천 문서, 종목 상세, 추천 상세, 세부 구조화 결과로 이동하는 링크가 보인다.
- [x] 주문 차단/읽기 전용 경계가 첫 화면에서 보인다.
- [x] local verification과 EC2 route smoke가 통과한다.
