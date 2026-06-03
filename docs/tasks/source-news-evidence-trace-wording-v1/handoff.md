# source-news-evidence-trace-wording-v1 Handoff

## Current Status

- completed: local implementation, EC2 deployment, route smoke, browser wording smoke, and AWH verification are complete.

## Decisions

- This is a wording and evidence-trace clarity task only.
- Keep the existing page structure and API contracts.
- Use `AI 근거`, `AI 구조화`, `근거 상세`, `수집 목록`, `보유 상태`, and `가상 매매` consistently.
- Preserve validator and order-boundary language. Do not imply that source documents approve recommendations or orders.

## Changes

- `/events` now describes source news as a `수집 목록` and AI state as `AI 구조화`/`AI 근거`.
- `/events/classification` now describes tag review as `태그와 방향 확인` and AI comparison as `AI 근거와 비교`.
- `/source-documents/[documentId]` now presents the source page as `원천 문서 근거 상세`, with `한국어 근거 요약`, `근거 발췌`, and `AI 근거 연결`.
- `/ai-evidence/results` now uses `보유 상태`, `가상 매매`, and `근거 묶음` wording.
- `NewsEventCard` now labels unstructured items as `AI 구조화 전` and evidence links as `AI 근거 상세`.

## Verification

- passed: text scan found no `AI 판단`, `검토서`, `검수`, `보유검토`, `페이퍼`, `AI 증거`, `AI 후보`, `AI 분석 전`, `추천 승인`, `수집 원장`, `AI 분석 목록`, `원문 다운로드`, `검토 발췌`, `검토 요약`, `연결된 증거`, `원장 보기`, or `미검토` in the target route/component files.
- passed: `cd apps/web && npm run typecheck`.
- passed: `cd apps/web && npm run build`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`.
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`.
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task source-news-evidence-trace-wording-v1`.
- passed: EC2 deployed commit `eeae672`; `npm run typecheck` and `npm run build` passed on `/opt/stockanalysis/app/apps/web`.
- passed: EC2 services active after restart: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`.
- passed: EC2 internal route smoke returned 200 for `/events`, `/events/classification`, `/ai-evidence/results`, and `/source-documents/source-document-rss%3Amarketwatch-topstories%3Aaf5c52a13d13ce24115656b8`.
- passed: local tunnel route smoke returned 200 for the same four routes at `http://127.0.0.1:13000`.
- passed: `/api/data-health` still reports `open_gates=[]`, `alert_destination.status=external_destination_verified`, and `news_ai_eval_quality.status=passed`.
- passed: Playwright browser text smoke on the four routes found zero old terms and confirmed the intended terms:
  - `/events`: `수집 목록`, `AI 근거 목록`, `AI 구조화 전`, `AI 근거 연결`.
  - `/events/classification`: `태그와 방향 확인`, `AI 근거와 비교`, `AI 근거 목록`.
  - `/ai-evidence/results`: `보유 상태`, `가상 매매`, `근거 묶음`.
  - `/source-documents/source-document-rss%3Amarketwatch-topstories%3Aaf5c52a13d13ce24115656b8`: `원천 문서 근거 상세`, `한국어 근거 요약`, `AI 근거 연결`.

## Next Step

- exact next step: continue the broader UX audit on the next page group. Suggested order is `/ai-evidence`, `/ai-evidence/[evidenceId]`, `/ai-evidence/blocked`, then `/data-health` if operational wording still feels like user-facing investment guidance.
