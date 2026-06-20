# professional-analysis-home-ux-v1 Contract

## Task Request

- request: 홈 화면을 전문 주식 분석 사이트처럼 보이게 재구성하고, 사용자가 무엇을 먼저 봐야 하는지 바로 알 수 있게 한다.

## Goal

- goal: `/`는 운영 로그형 카드 나열이 아니라 리서치 데스크 구조로 표시된다. 사용자는 첫 화면에서 오늘 결론, 확인 순서, 분석 패킷, 보완 큐를 순서대로 읽고 다음 화면으로 이동할 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/professional-analysis-home-ux-v1/*`

## Invariants

- Do not change DB schema.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions.
- Do not change portfolio positions.
- Do not change broker/order flow or live trading.
- Do not add paid external services.

## Scope

- 포함:
  - 홈 상단을 투자 리서치 데스크 구조로 재배치
  - 중복되는 상태 rail, 상세 입구, 판단 기준 섹션을 압축
  - 핵심 분석 패킷을 시장, 뉴스 AI, 사이클, 추천, 거래 안전으로 분리
  - 보완 큐를 홈 하단의 작업 큐로 유지하되 전문 분석 화면 톤으로 조정
- 제외:
  - `/intelligence`, `/ai-evidence`, `/cycle-map`, `/recommendations` 상세 재설계
  - 데이터 수집/AI 분석 로직 변경
  - 추천 산식 변경
  - 실거래 활성화

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-analysis-home-ux-v1`
- verification command: browser smoke for `/`

## Done Criteria

- [ ] `/` 첫 화면에 오늘 결론과 다음 행동 CTA가 명확히 보인다.
- [ ] `/`에서 수집, 시장, 뉴스 AI, 사이클, 추천, 거래 안전 순서가 한 화면 흐름으로 보인다.
- [ ] 운영 로그성 반복 문구가 줄고, 전문 분석 사이트처럼 보이는 리서치 패킷 구조가 적용된다.
- [ ] 검증 명령과 route/browser smoke가 통과한다.

