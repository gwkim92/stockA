# trading-readiness-boundary-clarity-v2 Contract

## Task Request

- request: `/trading-readiness` 화면에서 실제 주문 경계, broker submit 차단, kill switch, audit boundary를 첫 화면에 명확히 표시한다.

## Goal

- goal: `/trading-readiness` 첫 화면에서 실거래가 가능한지, 무엇이 차단하고 있는지, 증권사 제출이 비활성인지, 감사/페이퍼 검증이 어떤 상태인지 한눈에 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/trading-readiness-boundary-clarity-v2/*`

## Invariants

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- DB schema, FastAPI contract, scheduler, data ingest, AI batch runtime은 변경하지 않는다.
- 화면은 저장된 read-only 거래 준비 상태만 조합하며 실제 주문 버튼이나 쓰기 기능을 추가하지 않는다.

## Scope

- `/trading-readiness` 상단에 `실거래 경계 판정판`을 추가한다.
- 판정 축은 `실거래 결론`, `증권사 제출`, `킬 스위치`, `감사·페이퍼`로 고정한다.
- 기존 안전 조건, 증권사/계좌, 주문 한도, kill switch, paper validation 상세는 유지한다.
- 모바일에서 판정 카드가 1열로 내려오도록 CSS를 추가한다.

## Non-Goals

- broker submit 구현 금지
- kill switch 상태 변경 금지
- order limit policy 변경 금지
- audit write 구현 금지

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-boundary-clarity-v2`
- verification command: `git diff --check`
- verification command: EC2 또는 local tunnel에서 `/trading-readiness` route smoke

## Done Criteria

- [ ] `/trading-readiness` 상단에 `실거래 경계 판정판`이 렌더링된다.
- [ ] `실거래 결론`, `증권사 제출`, `킬 스위치`, `감사·페이퍼`가 첫 화면에 보인다.
- [ ] broker submit과 실제 주문 전송 상태가 명확히 보인다.
- [ ] local verification과 EC2 route smoke가 통과한다.
