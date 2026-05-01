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
- live DB adapter, write endpoint, auth/RBAC, production deployment는 아직 없다.

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

- Server Components fetch fixture DTOs through `apps/web/src/lib/frontend-api.ts`.
- Default API base URL is `http://127.0.0.1:8765`.
- Override with `STOCKANALYSIS_FRONTEND_API_BASE_URL`.
- Browser code does not receive database credentials or model API keys.
- Pages are marked dynamic because fixture server data is runtime data.

## UX Boundary

The initial UI is an investment cockpit shell, not a retail trading screen.

It prioritizes:

- open remediation tickets.
- critical blind spots.
- scheduler/data health.
- cycle state context.
- source run provenance.

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
- frontend architecture/API/adapter/fixture server regression checks.

## Next Steps

1. Browser QA in the in-app browser with fixture server and Next dev server.
2. Add detail routes for recommendation, thesis, portfolio coverage, and AI evidence.
3. Add live DB read adapter behind the same frontend DTO contract.
4. Add auth/RBAC before any write endpoint.
