# Task Contract

## Task

- 이름: frontend-equity-research-experience-v2
- 요청: 종목 상세와 추천 상세를 전문 주식 리서치 보고서 흐름으로 재구성한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/stocks/[symbol]`와 `/recommendations/[recommendationId]`에서 `사업 -> 재무 품질 -> 피어/경쟁 -> 밸류에이션 -> 뉴스/사이클 -> thesis -> 페이퍼 검증` 순서로 근거를 읽을 수 있다.

## Why

- 현재 프로젝트는 뉴스·AI·사이클 화면이 강해졌지만, 전문 애널리스트식 기업 분석 흐름이 화면에서 바로 보이지 않는다.
- 중장기 투자 판단은 뉴스 신호만으로 충분하지 않으므로 사업, 재무 품질, 밸류에이션, thesis, 페이퍼 검증 경계가 같은 순서로 보여야 한다.
- 사용자용 문구와 개발자용 문구가 섞이면 무엇을 봐야 하는지 이해하기 어렵다.

## Scope

- 포함:
  - 공통 리서치 흐름 UI 컴포넌트 추가
  - 종목 상세 화면 상단 분석 순서 재구성
  - 추천 상세 화면 상단 분석 순서 재구성
  - 기존 저장 DTO 기반 한국어 문구 정리
  - task contract/handoff 갱신
- 제외:
  - DB schema 변경
  - 추천 score formula 또는 component weight 변경
  - benchmark/evaluation 기준 변경
  - 신규 AI 호출
  - 실거래 broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/components/professional-research-flow.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/frontend-equity-research-experience-v2/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - recommendation scoring formulas
  - benchmark/evaluation 기준
  - live broker/order implementation
  - EC2 secret/env files

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-equity-research-experience-v2`
  - EC2 route smoke for `/stocks/NVDA` and `/recommendations/recommendation-140`

## Done Criteria

- [ ] `/stocks/[symbol]`에 전문 리서치 흐름이 표시된다.
- [ ] `/recommendations/[recommendationId]`에 전문 리서치 흐름이 표시된다.
- [ ] 리서치 artifact가 없는 경우에도 부족한 근거가 한국어로 설명된다.
- [ ] 자동 주문 또는 실거래 가능으로 오해될 문구가 없다.
- [ ] 로컬 검증과 EC2 route smoke가 통과한다.

## Risks

- 화면은 기존 저장 데이터를 재배치할 뿐, 기업 재무 모델 자체의 품질을 새로 높이지 않는다.
- 피어 비교와 밸류에이션은 현재 component/artifact 품질에 의존한다.
- outcome/evaluation 표본이 부족하므로 추천 weight는 변경하지 않는다.

