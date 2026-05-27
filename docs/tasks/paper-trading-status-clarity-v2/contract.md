# paper-trading-status-clarity-v2 Contract

## Task Request

- request: `/paper-trading` 화면에서 페이퍼 거래가 테스트 중인지, 차단됐는지, 실행 가능한 상태인지 첫 화면에서 명확히 구분되게 한다.

## Goal

- goal: `/paper-trading` 첫 화면에서 실제 주문 전송 여부, 가상 검증 상태, 실거래 차단 조건, 다음 확인 위치를 한눈에 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/paper-trading-status-clarity-v2/*`

## Invariants

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- DB schema, FastAPI contract, scheduler, data ingest, AI batch runtime은 변경하지 않는다.
- 화면은 저장된 read-only 페이퍼 검증 결과만 조합하며 실제 주문 버튼이나 쓰기 기능을 추가하지 않는다.

## Scope

- 중복되는 상단 판단 strip을 제거한다.
- `/paper-trading` 상단에 `페이퍼 거래 판정판`을 추가한다.
- 판정 축은 `실제 주문`, `페이퍼 검증`, `차단 조건`, `다음 행동`으로 고정한다.
- 기존 후보 목록, 위험 예산, 차단 사유, 추천/논리 링크는 유지한다.
- 모바일에서 판정 카드가 1열로 내려오도록 CSS를 추가한다.

## Non-Goals

- broker submit 구현 금지
- paper validation 알고리즘 변경 금지
- portfolio position/target weight 변경 금지
- 주문 한도, kill switch, audit write 변경 금지

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-v2`
- verification command: `git diff --check`
- verification command: EC2 또는 local tunnel에서 `/paper-trading` route smoke

## Done Criteria

- [x] `/paper-trading` 상단에 `페이퍼 거래 판정판`이 렌더링된다.
- [x] `실제 주문`, `페이퍼 검증`, `차단 조건`, `다음 행동`이 첫 화면에 보인다.
- [x] 실제 주문 전송 0건 또는 경고 상태가 명확히 보인다.
- [x] local verification과 EC2 route smoke가 통과한다.
