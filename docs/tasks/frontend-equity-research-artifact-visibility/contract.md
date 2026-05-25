# Task Contract

## Task

- 이름: frontend-equity-research-artifact-visibility
- 요청: `ai-equity-research-reporting`이 생성한 기업 리서치 artifact를 종목 상세 API와 화면에서 투자자가 이해 가능한 한국어 분석서 형태로 노출한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/stocks/{symbol}` live payload가 최신 `research.equity_research_artifact`를 `equity_research`로 반환하고, Next.js 종목 상세 화면이 사업/재무/촉매/리스크/밸류에이션 민감도 요약을 `AI 기업 분석 리포트` 섹션으로 보여준다.

## Scope

- 포함:
  - stock detail live adapter SQL에 최신 equity research artifact 조회 추가
  - stock detail DTO payload builder와 frontend type 확장
  - 종목 상세 화면의 한국어 리서치 섹션 추가
  - live adapter contract test 갱신
  - EC2 API/route smoke
- 제외:
  - 리서치 artifact 생성 runner 변경
  - 추천 total score나 component weight 변경
  - 신규 재무/밸류에이션 산출 방식 변경
  - broker/live order submit
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/frontend-equity-research-artifact-visibility/*`
- 수정 금지 파일:
  - 추천 점수 산식과 weight
  - `research.equity_research_artifact` schema
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-equity-research-artifact-visibility`

## Done Criteria

- 종목 상세 API는 최신 기업 리서치 artifact를 opaque id와 숫자/배열 정규화 형태로 반환한다.
- 종목 상세 화면은 AI가 생성한 기업 분석을 뉴스/가격/상위 흐름과 분리해서 보여준다.
- 화면은 해당 리서치가 배치 산출물이며, 추천 점수나 주문을 직접 바꾸지 않는다는 경계를 명확히 쓴다.
- Codex OAuth, fixture provider 모두 provider 정보를 노출하되 시크릿은 노출하지 않는다.
