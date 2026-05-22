# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - recommendation detail DTO에 `evidence_trace`를 추가했다.
  - `evidence_trace`는 직접 뉴스/AI, 상위 흐름 전파, 보유검토 상태를 분리한다.
  - `/recommendations/[recommendationId]`에 “근거 흐름 요약” 패널을 추가했다.
  - focused backend contract test, full unittest, Next typecheck/build를 통과했다.
  - EC2에 `765c5e4`를 배포하고 Next 서비스를 rebuild/restart했다.
  - EC2 API와 브라우저에서 추천 상세 evidence trace가 정상 표시됨을 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- recommendation detail SQL에서 기존 canonical table만 읽어 direct event/AI anchor, propagated macro-flow count, latest portfolio review item을 요약한다.
- response builder에서 raw DB id를 opaque frontend id로 정규화한다.
- 화면에서는 원천 ID보다 “무엇을 보고 검토해야 하는가”를 먼저 보여준다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `PYTHONPATH=src /private/tmp/stockanalysis-test-venv/bin/python -m unittest discover -s tests` ran 739 tests.
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-evidence-trace-summary`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `765c5e4`; `stockanalysis-web.service` active.
- PASS: EC2 focused backend tests and Next build.
- PASS: EC2 API `/api/recommendations/recommendation-52`
  - `symbol=SPY`
  - direct evidence `ai-evidence-75`
  - macro flow count `29`
  - macro preview count `8`
  - holding status `not_in_portfolio`
- PASS: Browser smoke `http://127.0.0.1:13000/recommendations/recommendation-52`
  - shows `근거 흐름 요약`
  - shows `무엇을 보고 이 추천을 검토해야 하나`
  - shows `뉴스/AI 분석`
  - shows `상위 흐름 전파`
  - shows `보유검토 연결`
  - shows `미국 시장 참여도 흐름이 종목 노출도 규칙을 거쳐 점수 입력으로 들어갔다.`

## Remaining

- 없음.

## Exact Next Step

- exact next step: continue with broader recommendation and holding-review quality work, especially surfacing which accepted AI/news evidence is absent from portfolio review and why.
