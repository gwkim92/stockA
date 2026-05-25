# Task Contract

## Task

- 이름: portfolio-risk-budget-policy-v2
- 요청: 포트폴리오 커버리지 화면을 단일 종목 비중 확인에서 섹터/테마 집중도와 리밸런싱 정책까지 보는 위험 예산 화면으로 확장한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/portfolio/{portfolio}/coverage` live payload가 단일 종목 한도뿐 아니라 섹터/테마 집중도, 미분류 노출, 리밸런싱 우선순위를 반환하고, Next.js 포트폴리오 커버리지 화면이 이를 한국어로 이해 가능하게 보여준다.

## Scope

- 포함:
  - 기존 `portfolio.position_snapshot`과 `ref.instrument_classification_membership`를 읽어 섹터/테마 노출도 계산
  - `risk_budget` DTO에 concentration policy와 exposure summary 추가
  - 화면에 섹터/테마 집중도와 리밸런싱 우선순위 섹션 추가
  - live adapter contract test와 frontend type 갱신
  - 로컬 검증, AWH 검증, EC2 API/route smoke
- 제외:
  - 신규 DB schema/migration
  - 추천 score/weight 변경
  - 자동 리밸런싱/주문 실행
  - 브로커 계좌 연동
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/portfolio-risk-budget-policy-v2/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-policy-v2`

## Done Criteria

- 포트폴리오 coverage API는 단일 종목 한도, 섹터 집중, 테마 집중, 미분류 노출, 리밸런싱 우선순위를 함께 반환한다.
- 화면은 사용자가 “어느 종목이 너무 큰가”, “어느 섹터/테마에 몰렸는가”, “어떤 보유가 우선 검토 대상인가”를 읽을 수 있어야 한다.
- 섹터/테마 미분류는 숨기지 않고 데이터 품질 gap으로 노출한다.
- 어떤 항목도 실제 주문이나 리밸런싱을 자동 실행하지 않는다.
