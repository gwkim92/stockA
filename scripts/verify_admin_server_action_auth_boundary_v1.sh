#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

actions_file="apps/web/src/app/admin/ai-agents/actions.ts"
panel_file="apps/web/src/app/admin/ai-agents/CodexOauthOperatorPanel.tsx"

if [[ -e "$actions_file" ]]; then
  echo "browser-callable admin Server Action file still exists: $actions_file" >&2
  exit 1
fi

if rg -n "^[[:space:]]*['\"]use server['\"];?[[:space:]]*$" apps/web/src; then
  echo "apps/web still contains a Server Action directive" >&2
  exit 1
fi

if rg -n 'STOCKANALYSIS_FRONTEND_API_ADMIN_ACTION_TOKEN|X-Stockanalysis-Admin-Action-Token|/__admin/codex-oauth|fetchFrontendRaw|postFrontendAdminAction|startCodexOauthRelogin|runCodexOauth(Direct|News)Smoke' apps/web/src; then
  echo "apps/web still contains the privileged admin POST/token surface" >&2
  exit 1
fi

if rg -n "^[[:space:]]*['\"]use client['\"];?|<button|<form|auth_url|user_code|device_auth_pid|status_path|last_error_summary" "$panel_file"; then
  echo "Codex OAuth status panel still exposes a client mutation or sensitive raw field" >&2
  exit 1
fi

node -e '
  const pkg = require("./apps/web/package.json");
  if (pkg.scripts?.start !== "next start -H 127.0.0.1") {
    throw new Error(`Next start must bind loopback, got: ${pkg.scripts?.start}`);
  }
'

if ! rg -F 'browser-reachable Next Server Actions are prohibited' docs/frontend-architecture.md >/dev/null; then
  echo "frontend architecture does not record the Server Action prohibition" >&2
  exit 1
fi

if ! rg -F 'internal Codex OAuth relogin and smoke operations remain out-of-band server CLI/SSH actions' \
  docs/frontend-api-contract.md >/dev/null; then
  echo "frontend API contract does not record the CLI/SSH-only mutation boundary" >&2
  exit 1
fi

if [[ -f apps/web/.next/server/server-reference-manifest.json ]] && \
  rg -n 'admin/ai-agents/actions|startCodexOauthReloginAction|runCodexOauth(Direct|News)SmokeAction' \
    apps/web/.next/server/server-reference-manifest.json; then
  echo "production build still registers removed admin Server Actions" >&2
  exit 1
fi

echo "admin server action auth boundary verification passed"
