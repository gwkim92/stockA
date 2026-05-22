# Session Handoff

## Current Status

- 상태: deployed_and_smoked
- 기준일: 2026-05-22
- 완료:
  - 영어 원문 제목을 제거하지 않고 원문 추적성은 유지하기로 했다.
  - 화면에서는 원문 제목과 한국어 판단 해석을 분리하는 방향으로 고정했다.
  - `NewsTitleBlock` 공용 컴포넌트를 추가해 `원문 제목`, `AI 요약`, `화면 해석`을 분리 표시한다.
  - `/ai-evidence`, `/events`, `/intelligence`, `/ai-evidence/[evidenceId]`, `/stocks/[symbol]`에 적용했다.
  - 긴 영어 제목이 줄바꿈되도록 CSS overflow wrapping을 추가했다.

## Verification Log

- PASS: local `cd apps/web && npm run typecheck`.
- PASS: local `cd apps/web && npm run build`.
- PASS: local `git diff --check`.
- PASS: local `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-title-interpretation-ui`.
- PASS: commit/push `04e532b`.
- PASS: EC2 pull to `04e532b`.
- PASS: EC2 `cd apps/web && npm run typecheck && npm run build`.
- PASS: EC2 `stockanalysis-web.service` and `stockanalysis-frontend-api.service` active.
- PASS: EC2 page smoke 200: `/intelligence`, `/events`, `/ai-evidence`, `/ai-evidence/ai-evidence-122`, `/stocks/SPY`.
- PASS: EC2 rendered content contains `원문 제목` and `화면 해석`.

## Exact Next Step

- exact next step: continue page-by-page copy review for remaining non-news raw labels, especially recommendation detail and source document detail pages.
