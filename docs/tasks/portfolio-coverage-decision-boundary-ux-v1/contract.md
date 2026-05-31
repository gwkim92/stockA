# portfolio-coverage-decision-boundary-ux-v1

## Task Request

- request: 전체 UX/UI 리팩터링 흐름에서 `/portfolio/coverage` 화면을 이어서 정리한다.

## Goal

- goal: 포트폴리오 커버리지 화면에서 보유 검토, 리스크 예산, 리밸런싱 후보, 성과 성숙 대기, 추천 산식 변경 금지, 주문 차단 경계를 사용자가 바로 이해하게 만든다.

핵심 질문은 아래 네 가지다.

- 어떤 보유 종목이 투자 논리와 성과 측정으로 커버되는가?
- 어떤 종목/섹터/테마가 위험 예산을 넘거나 검토가 필요한가?
- 리밸런싱 후보가 주문 지시가 아니라 검토 후보임을 알 수 있는가?
- 추천 산식 가중치 변경과 증권사 주문 전송이 왜 아직 차단되는가?

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `docs/tasks/portfolio-coverage-decision-boundary-ux-v1/*`

## Non-Goals

- recommendation score component weight 변경 금지
- broker/order submit 활성화 금지
- portfolio position, benchmark, outcome record 변경 금지
- paper validation, calibration, review runner 로직 변경 금지
- DB schema, API DTO, scheduler cadence 변경 금지

## Acceptance Criteria

- `/portfolio/coverage` 상단 판정판에서 투자 논리/성과 커버리지, 위험 예산, 리밸런싱 후보, 추천 산식 변경 금지 상태가 한국어로 보인다.
- 사용자 화면의 `thesis`, `outcome`, `weight`, `broker`, `feedback`, `calibration`, `cadence`, `action router`, `source 없음` 같은 내부/혼합 표현이 주요 영역에서 사용자 문장으로 바뀐다.
- 리밸런싱 후보와 포지션 크기 후보의 이유가 raw backend text가 아니라 한국어 이유로 보인다.
- 검증은 Next typecheck/build, AWH task verify, EC2 route smoke로 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-boundary-ux-v1`
- verification command: EC2 route/content smoke for `/portfolio/coverage`
