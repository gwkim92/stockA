# Session Handoff

## Current Status

- 상태: in_progress
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

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `git diff --check`
- PASS: `cd apps/web && npm run build`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-cockpit-feature-map-and-ai-gates`

## Exact Next Step

- exact next step: deploy to EC2 and smoke key pages through the running app.
