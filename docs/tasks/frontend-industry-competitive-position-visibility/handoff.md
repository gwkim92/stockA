# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - stock detail/recommendation detail live SQL에 `research.industry_competitive_position` 최신 row를 연결했다.
  - `StockDetailData`와 `RecommendationDetailData`에 `industry_competitive_position` DTO를 추가했다.
  - 종목 상세와 추천 상세에서 산업 경쟁 위치, 피어 그룹, 강점, 리스크, 경쟁력/리스크 추정 점수를 한국어로 표시한다.
  - 로컬 focused tests, Next typecheck/build, compileall, diff check, AWH verify를 통과했다.
  - EC2에 배포하고 stock detail API/route smoke를 확인했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 현재 최신 추천 상세에서 산업 경쟁 포지션 실데이터를 보려면 2026-05-25 기준 추천 배치가 필요하다.
  - `decision-daily` 재실행은 첫 단계 `missing-symbol-price-backfill`에서 `BRK-A`가 Twelve Data invalid symbol로 실패해 추천 생성 단계까지 가지 못했다. stock detail은 최신 산업 경쟁 포지션을 정상 표시한다.

## Decisions

- 산업 경쟁 포지션은 확정 애널리스트 판단이 아니라 피어/재무 기반 deterministic 추정 지표로 표시한다.
- 추천 score/weight는 변경하지 않는다.
- 화면 진입 중 AI를 호출하지 않는다. 배치가 저장한 값을 읽기 전용으로 보여준다.

## Exact Next Step

- exact next step: `market-price-invalid-symbol-tolerance` 또는 동등한 작은 수정으로 Twelve Data가 거부하는 `BRK-A` 같은 심볼을 전체 `decision-daily` 실패로 만들지 않게 한 뒤, 2026-05-25 `decision-daily`를 재실행하고 최신 추천 상세에서 산업 경쟁 포지션이 실제 추천 기준일에 붙는지 확인한다. 그 다음 `recommendation-quality-calibration`으로 돌아가 산업 경쟁 포지션/재무/밸류에이션 점수 항목의 성과 설명력을 측정한다. 추천 가중치는 평가 전까지 계속 0으로 둔다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - 결과: `Ran 58 tests ... OK`
- `cd apps/web && npm run typecheck`
  - 결과: 통과
- `cd apps/web && npm run build`
  - 결과: Next production build 통과
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - 결과: 통과
- `git diff --check`
  - 결과: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-industry-competitive-position-visibility`
  - 결과: `Task frontend-industry-competitive-position-visibility passed readiness checks.`
- GitHub/EC2 배포
  - commit: `2caa1c2 Expose industry competitive position in detail views`
  - push: `codex/local-mvp-runtime-aws-bootstrap -> origin/codex/local-mvp-runtime-aws-bootstrap`
  - EC2 `/opt/stockanalysis/app` fast-forward pull 성공
- EC2 verification
  - `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
    - 결과: `Ran 58 tests ... OK`
  - `cd apps/web && npm run typecheck && npm run build`
    - 결과: 통과
  - `sudo systemctl restart stockanalysis-frontend-api.service stockanalysis-web.service`
    - 결과: 두 서비스 모두 `active`
  - FastAPI stock detail smoke
    - `/api/stocks/NVDA`에서 `industry_competitive_position` 반환 확인: `NVDA advantaged Technology 0.6979 pipeline-run-791`
  - Next route smoke
    - `/stocks/NVDA`: `200`, `산업 경쟁 위치` 포함
    - `/recommendations/recommendation-140`: `200`, 산업 경쟁 위치 섹션 포함. 단 추천 기준일이 2026-05-23이라 최신 2026-05-25 산업 경쟁 row는 look-ahead 방지 때문에 붙지 않음.
    - `/data-health`: `200`
- EC2 residual blocker
  - `decision-daily --as-of-date 2026-05-25 --execute`는 `BRK-A` Twelve Data invalid symbol 때문에 `missing-symbol-price-backfill` 단계에서 실패했다.
  - artifact: `/opt/stockanalysis/artifacts/20260525T122251Z_market-price-daily/`
  - 원인: 전체 59개 누락 가격 중 `AMD`, `ARM`, `CART`는 성공했지만 `BRK-A` 한 건이 provider invalid symbol로 실패하고 나머지는 무료 요청 한도 때문에 skipped.
