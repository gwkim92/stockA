# ai-evidence-path-workbench-v4 Handoff

## Status

- completed and deployed to EC2.

## Current Status

- 상태: local verification, EC2 deploy, route smoke, and in-app browser smoke passed.
- 기준일: 2026-06-14
- 완료:
  - task contract created.
  - added reusable `EvidencePathWorkbench` for the fixed source -> translation -> AI structure -> validator -> recommendation/order path.
  - applied the workbench to `/ai-evidence/[evidenceId]`.
  - applied the workbench to `/ai-evidence/results`.
  - applied the workbench to `/ai-evidence/blocked`.
  - added mini evidence paths to news cluster cards in `/ai-evidence/results`.
  - added responsive CSS for the shared workbench and mini paths.
  - deployed commit `bc09fca5` to EC2 `develop`.
- 막힌 점:
  - none.

## Verification

- Passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-path-workbench-v4`
  - EC2 rebuild/restart: `npm run typecheck && npm run build && sudo systemctl restart stockanalysis-web.service`; service state `active`; commit `bc09fca5`
  - EC2 route smoke:
    - `/ai-evidence`: `뉴스 AI 근거`, `확인 순서`, `원천 뉴스`, `AI 구조화`; server error absent
    - `/ai-evidence/results`: `통과 결과를 읽는 순서`, `원천 뉴스`, `한국어 번역`, `AI 구조화`, `자동 검증`, `추천·주문 경계`; server error absent
    - `/ai-evidence/blocked`: `차단 항목을 읽는 순서`, `원천 보존`, `한국어 확인`, `차단 사유`, `후속 조치`, `자동 주문 영향 없음`; server error absent
    - `/ai-evidence/ai-evidence-1457`: `이 근거를 읽는 순서`, `원천 뉴스`, `한국어 번역`, `AI 구조화`, `자동 검증`, `추천·주문 경계`; server error absent
  - in-app browser smoke through `http://127.0.0.1:13000`:
    - `/ai-evidence/results` workbench shows `현재 통과 후보 80개 · 주문 경계는 계속 읽기 전용이다.`
    - `/ai-evidence/blocked` workbench shows `검증 차단 51개 · 저신호 보류 0개 · 자동 주문 영향 없음.`
    - `/ai-evidence/ai-evidence-1457` workbench shows `AI 검증 통과 항목 · 연결 종목 CDNS · 주문 경계 읽기 전용·주문 금지`

## Exact Next Step

- exact next step: continue the UX refactor on the next highest-friction screen: either `/recommendations/[id]` professional waterfall density or `/data-health` monitoring/attention grouping.

## Notes

- This is visibility-only. Do not change recommendation weights, benchmark definitions, portfolio positions, schema, or broker/order boundaries.
