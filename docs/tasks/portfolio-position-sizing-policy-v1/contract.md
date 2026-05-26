# Task Contract

## Task

- 이름: portfolio-position-sizing-policy-v1
- 요청: 리밸런싱 검토 후보를 실제 주문 수량이 아니라 thesis quality, valuation margin, active risk, liquidity/cash buffer를 반영한 position sizing review envelope로 연결한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/portfolio/{portfolio}/coverage`와 `/portfolio/coverage`에서 각 보유 종목을 “축소 검토”, “증거 보강 전 증액 금지”, “작은 비중 관찰”, “유지 검토”로 구분하고, 그 이유를 투자 논리·기업 분석·밸류에이션·벤치마크 괴리 기준으로 설명한다.

## Scope

- 포함:
  - `risk_budget.position_sizing_review` DTO 추가
  - 보유 포지션별 thesis 연결 여부, latest professional recommendation component, latest valuation snapshot, latest equity research artifact, benchmark active weight를 결합
  - 후보별 `review_band`, `blocking_factors`, `supporting_factors`, `rationale`, read-only order boundary 노출
  - `/portfolio/coverage`에 한국어 포지션 크기 검토 섹션 추가
  - unit/adapter/frontend type/build 검증
- 제외:
  - 추천 scoring formula/weight 변경
  - 자동 리밸런싱 목표 비중 또는 주문 수량 산출
  - broker submit, live order, kill switch unlock
  - 새 DB schema
  - benchmark/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `docs/tasks/portfolio-position-sizing-policy-v1/*`
  - `docs/plans/2026-05-26-portfolio-position-sizing-policy-v1.md`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - broker/order submit path
  - repo 안 secret/env 값
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-position-sizing-policy-v1`
  - `git diff --check`

## Done Criteria

- API DTO가 position sizing review envelope를 만든다.
- 후보는 read-only이며 `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`를 가진다.
- 화면은 포지션 크기 검토를 주문 후보가 아니라 투자 근거 검토로 설명한다.
- 추천 weights, broker submit, automatic order flags는 변경되지 않는다.
- EC2 API/route smoke에서 `position_sizing_review`와 화면 섹션이 확인된다.
