# Task Handoff

## Current Status

- 완료:
  - 공통 리서치 흐름 컴포넌트를 추가했다.
  - 종목 상세와 추천 상세 상단을 전문 분석서 순서로 재구성했다.
- 진행 중:
  - 로컬 검증 후 EC2 route smoke를 남긴다.
- 막힌 점:
  - 없음.

## Current Decision

- 새 분석 모델, schema, 추천 weight는 만들지 않는다.
- 기존 기업 리서치, 추천 component, 뉴스/사이클, thesis, 페이퍼 경계를 한 화면에서 읽기 쉬운 순서로 재배치한다.
- 실거래 broker submit은 계속 닫힌 상태로 표현한다.

## Changed Files

- `apps/web/src/components/professional-research-flow.tsx`
- `apps/web/src/app/stocks/[symbol]/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/frontend-equity-research-experience-v2/contract.md`
- `docs/tasks/frontend-equity-research-experience-v2/handoff.md`

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`: pass
- `cd apps/web && npm run typecheck`: pass
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: pass
- `git diff --check`: pass
- `cd apps/web && npm run build`: pass
- `awh verify`: first run failed because contract/handoff headings were incomplete; rerun after this update.

## Exact Next Step

- exact next step: AWH verify를 다시 실행한다. 이후 EC2에 배포해 `/stocks/NVDA`와 `/recommendations/recommendation-140` route smoke를 확인한다.

## Remaining Risks

- 실제 리서치 품질은 현재 저장된 financial/valuation artifact 품질에 의존한다.
- 추천 점수 반영 여부는 outcome/evaluation 표본이 충분해질 때까지 변경하지 않는다.
