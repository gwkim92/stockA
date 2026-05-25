# Task Contract

## Task

- 이름: recommendation-detail-equity-research-link
- 요청: 추천 상세에서 종목별 AI 기업 리서치 artifact까지 추적 가능하게 연결한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/recommendations/{id}` live payload가 최신 `research.equity_research_artifact`를 `equity_research`로 반환하고, Next.js 추천 상세 화면이 “기업 리서치 연결” 섹션에서 한국어 요약, 핵심 포인트, 촉매, 리스크, 무효화 조건, 밸류에이션 민감도를 보여준다.

## Scope

- 포함:
  - recommendation detail live adapter SQL에 latest equity research artifact 조회 추가
  - recommendation detail DTO와 frontend type 확장
  - 추천 상세 화면의 기업 리서치 연결 섹션 추가
  - live adapter contract test 갱신
  - EC2 API/route smoke
- 제외:
  - 리서치 artifact 생성 runner 변경
  - recommendation score, component weight 변경
  - 신규 재무/밸류에이션 산출 방식 변경
  - broker/live order submit
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/recommendation-detail-equity-research-link/*`
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
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-detail-equity-research-link`

## Done Criteria

- 추천 상세 API는 최신 기업 리서치 artifact를 opaque id와 배열/숫자 정규화 형태로 반환한다.
- 추천 상세 화면은 뉴스/사이클 근거, zero-weight fundamental component, AI 기업 리서치 artifact를 구분해서 보여준다.
- 화면은 이 artifact가 추천 점수나 주문을 직접 변경하지 않는 읽기 전용 분석임을 명확히 표시한다.
- Codex OAuth, fixture provider 모두 provider 정보를 노출하되 시크릿은 노출하지 않는다.
