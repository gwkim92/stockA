# Session Handoff

## Current Status

- 완료:
  - `/api/cycle-map` live read DTO 추가.
  - `/cycle-map` Next.js 화면 추가.
  - 홈, 뉴스·AI, 사이클 화면에서 cycle map으로 이동하는 링크 추가.
  - 대표 종목/최근 뉴스/관계선/주요 카운트는 AI 요약값 대신 canonical DB에서 계산하도록 hardening.
  - 뉴스 AI validator가 직접 종목 영향을 원문 제목/요약에 grounding하도록 강화.
  - EC2 오염 데이터 정리: 원문에 `XOM`/`Exxon` 근거가 없는 AI 직접 종목 연결 2건 삭제.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: 계층형 impact propagation/cycle snapshot이 새 validator 결과를 반영하도록 다음 scheduled run 이후 `/cycle-map`, `/stocks/*`, `/recommendations/*`를 재점검한다.

## Verification Evidence

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- EC2 DB SQL smoke: `AI_SEMICONDUCTOR_CYCLE` top symbols are `NVDA`, `MSFT`; `XOM` removed.
