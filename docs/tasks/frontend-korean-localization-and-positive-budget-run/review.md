# Frontend Korean Localization And Positive Budget Run Review

## Verification

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: local Next route smoke returned HTTP 200 for `/`, `/data-health`, `/remediation`, `/performance`, `/themes/ANNUAL_REPORTING`, `/ai-evidence/sec-event-aapl-10k-20240928`.
- PASS: rendered HTML contains Korean replacements including `주의 필요`, `사람 리스크 검토`, `로컬 제공자 예산 원장`, `완료`, `다음 포트폴리오 검토`.
- PASS: rendered HTML no longer contains the targeted old English phrases `attention required`, `Review exit`, `human risk review`, `local provider budget ledger`, `completed`, `production api server`, `auth rbac`, `alert destination`, `data operations artifact runner`, `exit review`, `Create or link an active thesis`.
- PASS: `git diff --check`

## Residual Risks

- pipeline names, run IDs, ticker symbols, provider names, model IDs, and storage identifiers remain in original English/code form intentionally.
- backend에서 새로 생성되는 자유문장 reason/summary는 이번 helper에 없는 경우 영어로 보일 수 있다.
- 모든 enum이 아니라 현재 cockpit에서 반복적으로 노출되는 값 위주로 매핑했다.
