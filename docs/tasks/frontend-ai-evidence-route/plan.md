# Implementation Plan

## Steps

1. Add AI evidence/source document DTO examples and contract index entries.
2. Extend frontend TypeScript types and API client functions.
3. Add `/ai-evidence/[evidenceId]` and `/source-documents/[documentId]` pages.
4. Link source-document evidence from recommendation and thesis detail routes.
5. Update docs, tests, and verification scripts for the expanded contract.
6. Run production route smoke, browser smoke, AWH verification, and placeholder scan.
7. Commit, push, review PR, and merge into `develop`.

## Verification

```bash
bash scripts/verify_frontend_detail_routes.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-ai-evidence-route
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
