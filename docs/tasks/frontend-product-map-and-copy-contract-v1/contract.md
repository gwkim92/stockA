# frontend-product-map-and-copy-contract-v1 Contract

## Request

- 전문 투자 리서치 UX/UI 전면 정상화 작업의 기준 문서를 만든다.
- 모든 route를 투자자 판단 화면과 운영 콘솔로 분리하고, route별 핵심 질문·첫 화면 결론·필수 데이터·금지 용어·빈 상태·오류 상태를 고정한다.

## Scope

- 투자자 화면: `/`, `/market-map`, `/cycle-map`, `/intelligence`, `/ai-evidence`, `/stocks`, `/stocks/[symbol]`, `/recommendations`, `/recommendations/[id]`, `/portfolio/coverage`, `/paper-trading`.
- 운영 콘솔: `/data-health`, `/admin/ai-agents`, `/trading-readiness`, `/remediation`.
- `DESIGN.md`의 component section을 현재 리서치 워크스페이스 기준으로 보강한다.

## Invariants

- Backend API, DB schema, recommendation score, benchmark, portfolio position, broker/order boundary는 변경하지 않는다.
- 투자자 화면에는 `pipeline`, `runner`, `artifact`, `fallback`, `canonical`, `shadow`, raw snake_case status code를 노출하지 않는다.
- 운영 콘솔에서는 내부 용어를 허용하되 사용자 행동과 장애 영향이 먼저 보여야 한다.

## Verification

- route role table exists in handoff.
- forbidden term table exists in handoff.
- `git diff --check`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-product-map-and-copy-contract-v1`
