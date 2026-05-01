# Apps Web Scaffold

이 문서는 첫 frontend app scaffold를 정의한다.

## Current Status

- `apps/web` Next.js App Router scaffold를 추가했다.
- app은 fixture server에서 read-only DTO를 fetch한다.
- initial routes:
  - `/`
  - `/remediation`
  - `/data-health`
  - `/cycles`
  - `/events`
  - `/themes/ANNUAL_REPORTING`
  - `/recommendations/AAPL-2024-11-01`
  - `/theses/AAPL-bootstrap-v1`
  - `/portfolio/coverage`
  - `/performance`
  - `/ai-evidence/sec-event-aapl-10k-20240928`
  - `/source-documents/aapl-2024-10k-20240928`
- local API runtime은 `--source fixture|live|auto`를 지원한다. `apps/web`은 같은 base URL을 바라보며, 서버 실행 source mode에 따라 fixture 또는 live-supported DTO를 받는다.
- write endpoint, auth/RBAC, production deployment는 아직 없다.

## Stack

- Next.js: `16.2.4`
- React: `19.2.5`
- TypeScript: `6.0.3`
- Node tested locally: `24.6.0`
- npm tested locally: `11.5.2`

Versions were checked from npm registry on 2026-05-01 before scaffold.

## Local Development

Start fixture server:

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port 8765
```

Start local runtime with auto live fallback:

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port 8765 \
  --source auto
```

Start web app:

```bash
cd apps/web
npm install --no-audit --fund=false
STOCKANALYSIS_FRONTEND_API_BASE_URL=http://127.0.0.1:8765 npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Data Boundary

- Server Components fetch read-only DTOs through `apps/web/src/lib/frontend-api.ts`.
- Default API base URL is `http://127.0.0.1:8765`.
- Override with `STOCKANALYSIS_FRONTEND_API_BASE_URL`.
- Browser code does not receive database credentials or model API keys.
- DB credentials, when used, stay in the Python local runtime process via `STOCKANALYSIS_PSQL_COMMAND`.
- Pages are marked dynamic because fixture server data is runtime data.

## UX Boundary

The initial UI is an investment cockpit shell, not a retail trading screen.

It prioritizes:

- open remediation tickets.
- critical blind spots.
- scheduler/data health.
- cycle state context.
- source run provenance.
- event/theme evidence chains.
- performance outcome accountability.

It intentionally does not implement:

- buy/sell chat recommendations.
- broker order placement.
- ticket status mutation.
- hidden thesis mutation.

## Verification

```bash
bash scripts/verify_apps_web_scaffold.sh
```

The verification script checks:

- web scaffold files.
- npm install.
- TypeScript check.
- Next production build.
- fixture server runtime.
- Next production server route smoke for `/`, `/remediation`, `/data-health`, `/cycles`.
- Detail route smoke for `/events`, `/themes/ANNUAL_REPORTING`, `/performance`, recommendation, thesis, coverage, AI evidence, and source document routes is covered by `scripts/verify_frontend_detail_routes.sh`.
- frontend architecture/API/adapter/fixture server regression checks.

Browser visual QA:

- report: `docs/tasks/frontend-browser-visual-qa/report.md`
- checked: desktop dashboard/events/theme/performance/coverage and mobile performance route.
- fixed: mobile horizontal overflow in global bento/nav layout.

## Next Steps

1. Expand live support to daily cockpit, data health, event/theme, and performance endpoints.
2. Add full accessibility audit for the expanded frontend.
3. Add auth/RBAC before any write endpoint.
