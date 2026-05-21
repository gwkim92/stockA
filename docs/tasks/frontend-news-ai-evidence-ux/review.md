# Review Notes

## Summary

- `news_event_candidate` artifacts now have an explicit AI evidence detail UX.
- Event list and intelligence trace now distinguish news AI candidates from generic AI evidence and show provider/confidence metadata.
- Wording now reflects the current flow: rule enrichment plus Codex OAuth offline candidate analysis, not local rules only.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: pass.
- `bash scripts/verify_frontend_api_contract.sh`: pass.
- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-news-ai-evidence-ux`: pass.
- EC2 DB direct SQL smoke for event list: pass.
- EC2 DB direct SQL smoke for `ai-evidence-10`: pass.
- EC2 deploy/build/service restart: pass, `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- EC2 API smoke for `/api/ai-evidence/ai-evidence-10`: pass, returned `news_event_candidate` with `codex_oauth` provider, candidate impacts, and retrieval context.
- Tunnel web smoke for `/ai-evidence/ai-evidence-10` and `/events`: pass, key Korean markers rendered.

## Remaining Risks

- This slice does not change scoring, recommendation generation, scheduler cadence, or broker/order flow.
