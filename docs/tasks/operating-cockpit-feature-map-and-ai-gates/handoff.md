# Session Handoff

## Current Status

- 상태: deployed_and_smoked
- 기준일: 2026-05-22
- 완료:
  - task contract를 만들었다.
  - 홈에 12개 기능 위치를 보여주는 기능 지도를 추가했다.
  - 데이터 수집 화면에 캔들, 뉴스 원문, 1차 분류, Codex OAuth 분석, validator, 추천 신호, 보유 검토 상태 카드를 추가했다.
  - 뉴스/AI 화면에 원문 수집, 1차 분류, Codex OAuth 분석, 검증, 추천 연결 순서 카드를 추가했다.
  - `/api/events`가 `news_event_candidate_rejected`와 `news_event_candidate_suppressed`를 read-only로 조회할 수 있게 확장했다.
  - AI 근거 목록에 통과 후보와 validator 차단/저신호 보류 후보를 분리해 표시했다.
  - AI 근거 상세에서 `news_event_candidate_rejected`도 candidate/retrieval context를 볼 수 있게 했다.
  - 가상 거래 화면에 현재 paper preview 단계와 브로커 제출 건수, 안전 관문 차단 수를 먼저 보여주는 상태 카드를 추가했다.
  - GitHub commit `20284f2`를 EC2에 fast-forward pull 했다.
  - EC2에서 Next production build를 재생성하고 `stockanalysis-web.service`를 재시작했다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `git diff --check`
- PASS: `cd apps/web && npm run build`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-cockpit-feature-map-and-ai-gates`
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- PASS: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- PASS: EC2 `stockanalysis-frontend-api.service`, `stockanalysis-web.service` active
- PASS: local tunnel smoke `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence`, `/paper-trading`, `/recommendations` all returned 200.
- PASS: local tunnel content checks found `서비스 기능 지도`, `수집/분석별 상태`, `뉴스 처리 흐름`, `차단/보류`, `현재 단계`.
- PASS: EC2 FastAPI smoke `/api/events?asOfDate=2026-05-22&evidenceType=news_event_candidate_rejected&limit=5` returned 200.
- PASS: EC2 FastAPI smoke `/api/events?asOfDate=2026-05-22&evidenceType=news_event_candidate_suppressed&limit=5` returned 200 and 5 events.

## Exact Next Step

- exact next step: continue copy/UX cleanup on lower-priority pages `/cycles`, `/performance`, `/themes/[themeKey]`, and `/source-documents/[documentId]`; then decide whether to add stored Korean AI summaries for English excerpts.
