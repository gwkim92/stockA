# Task Handoff

## Current Status

- 완료:
  - 공통 리서치 흐름 컴포넌트를 추가했다.
  - 종목 상세와 추천 상세 상단을 전문 분석서 순서로 재구성했다.
  - 로컬 검증, AWH 검증, EC2 배포와 route smoke를 완료했다.
- 진행 중:
  - 없음.
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
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-equity-research-experience-v2`: pass
- EC2 `git pull --ff-only origin codex/local-mvp-runtime-aws-bootstrap`: pass, deployed commit `b459465`
- EC2 `cd apps/web && npm run build`: pass
- EC2 `systemctl is-active stockanalysis-web.service`: active
- EC2 `systemctl is-active stockanalysis-frontend-api.service`: active
- EC2 route smoke: `/stocks/NVDA` 200 with `전문 리서치`, `사업 개요`, `재무 품질`, `밸류에이션`, `페이퍼 검증`
- EC2 route smoke: `/recommendations/recommendation-140` 200 with `전문 리서치`, `사업 개요`, `재무 품질`, `밸류에이션`, `페이퍼 검증`
- EC2 wording smoke: `/stocks/NVDA` includes `NVDA 분석은 종목 하나로 끝나지 않는다` and does not include `NVDA을`.

## Exact Next Step

- exact next step: `recommendation-quality-calibration`으로 넘어가 추천 outcome/성과 표본을 재현 가능하게 쌓고, 현재 weight 0인 fundamental/valuation/peer component를 언제 반영할지 평가 기준을 만든다.

## Remaining Risks

- 실제 리서치 품질은 현재 저장된 financial/valuation artifact 품질에 의존한다.
- 추천 점수 반영 여부는 outcome/evaluation 표본이 충분해질 때까지 변경하지 않는다.
