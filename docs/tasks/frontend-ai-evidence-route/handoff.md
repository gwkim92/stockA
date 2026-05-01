# Session Handoff

## Active Task

- 이름: frontend-ai-evidence-route
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - AI evidence/source document fixture DTO와 contract index endpoint를 추가했다.
  - `/ai-evidence/sec-event-aapl-10k-20240928`와 `/source-documents/aapl-2024-10k-20240928` read-only route를 추가했다.
  - recommendation/thesis detail에서 source-document event evidence를 AI evidence drilldown으로 연결했다.
  - 현재 Cursor가 적용한 dark bento frontend 스타일 방향을 유지하면서 route를 통합했다.
  - production route smoke, AWH, placeholder scan, Playwright smoke를 실행했다.
- 막힌 점:
  - 현재 없음.

## Files Touched

- 생성:
  - `docs/api/frontend/examples/ai-evidence-detail.json`
  - `docs/api/frontend/examples/source-document-detail.json`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/source-documents/[documentId]/page.tsx`
- 수정:
  - `docs/api/frontend/contract-index.json`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/apps-web-scaffold.md`
  - `docs/verification-plan.md`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - `scripts/verify_frontend_api_contract.sh`
  - `scripts/verify_frontend_detail_routes.sh`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_fixture_server.py`

## Decisions

- AI evidence route is an audit/provenance view, not a prompt execution UI.
- Source document route exposes metadata and excerpts only through fixture DTOs.
- LLM cost/token fields are display-only and must come from persisted run metadata.
- Cursor frontend restyle was preserved; only clear Next.js compatibility issues such as CSS font import were normalized.

## Verification Already Run

- `bash scripts/verify_frontend_api_contract.sh`: 통과
- `npm run typecheck` in `apps/web`: 통과
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-ai-evidence-route`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
- Playwright `/ai-evidence/sec-event-aapl-10k-20240928`: page title `AI Evidence | Stockanalysis Dashboard`, console errors 0, warnings 0.
- Playwright `/source-documents/aapl-2024-10k-20240928`: page title `Source Document | Stockanalysis Dashboard`, console errors 0, warnings 0.
- Screenshots captured under ignored `output/playwright/`.

## Still Unverified

- production visual QA. Current visual QA was Next dev server based; production route/build smoke is covered by `scripts/verify_frontend_detail_routes.sh`.

## Exact Next Step

- 다음 세션은 이것부터 시작: broader `/events` or `/themes/[themeKey]` explorer를 만들거나, live DB read adapter를 같은 DTO contract 뒤에 연결한다.

## Risks

- Known fixture IDs only.
- Live DB source document adapter remains outside this task.
