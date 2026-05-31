# data-health-monitoring-decision-ux-v1

## Task Request

- request: 전체 UX/UI 리팩터링 흐름에서 `/data-health` 화면을 이어서 정리한다.

## Goal

- goal: 데이터 상태 화면에서 수집, AI 분석, 품질 감사, 성과 대기, 주문/추천 산식 경계를 운영자 로그가 아니라 사용자 판단 순서로 이해하게 만든다.

핵심 질문은 아래 네 가지다.

- 자동 수집과 분석이 정상적으로 돌고 있는가?
- 뉴스/AI/품질 감사가 추천 입력으로 쓰일 만큼 통과했는가?
- 성과 표본이 부족해서 추천 산식 변경이 막힌 상태인가?
- 증권사 주문과 자동 리밸런싱은 계속 차단되는가?

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/tasks/data-health-monitoring-decision-ux-v1/*`

## Non-Goals

- scheduler cadence, profile, systemd service 변경 금지
- recommendation score component weight 변경 금지
- broker/order submit 활성화 금지
- pipeline runner, calibration, paper validation 로직 변경 금지
- DB schema, API DTO 변경 금지

## Acceptance Criteria

- `/data-health` 첫 화면에서 접근 경계, 자동 수집, 데이터·AI 품질, 투자 경계가 한국어 사용자 문장으로 보인다.
- 주요 사용자 영역의 `weight`, `broker`, `outcome`, `feedback`, `calibration`, `cadence`, `router`, `child runner`, `paper validation`, `thesis`, `artifact`, `gate` 같은 내부/혼합 표현이 줄어든다.
- 운영자 세부 로그는 유지하되, 첫 판단 영역은 “지금 뭘 봐야 하는가” 중심으로 읽힌다.
- 검증은 Next typecheck/build, AWH task verify, EC2 route smoke로 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-monitoring-decision-ux-v1`
- verification command: EC2 route/content smoke for `/data-health`
