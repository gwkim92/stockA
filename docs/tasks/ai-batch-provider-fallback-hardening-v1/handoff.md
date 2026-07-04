# ai-batch-provider-fallback-hardening-v1 Handoff

## 2026-07-04

- completed: `ai-batch-provider-fallback-hardening-v1` implemented, deployed, and smoke tested on EC2.
- exact next step: Continue with `manual-weight-review-pilot-decision-v1`; do not start `manual-weight-review-pilot-v1` until the user explicitly approves the pilot scope and read-only/no-order boundary.

Current status: complete and deployed to EC2.

Current EC2 AI state before code deploy:

- `openai_provider_health.status=openai_insufficient_quota`
- paid OpenAI API key and admin key are configured, but quota is exhausted.
- fallback provider is `codex_oauth`.
- local fallback provider is `local_rules`.
- `live_ai_invocation_health.status=recovered_with_recent_failures`
- `live_ai_invocation_health.attention_required=false`
- monitored critical tasks have latest successful runs:
  - `news-rss-korean-translation`
  - `news-rss-ai-extract`

Change:

- `stockanalysis-operations ai-agent-registry-report` now accepts `--env-file` and `--repo-root`, matching the rest of the AI/provider smoke commands.
- The env file is loaded through the existing repo-outside env policy and is not printed in the registry report.

Evidence:

- passed: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_ai_agent_registry_report_accepts_repo_outside_env_without_secrets`
- passed: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_openai_provider_health_report_is_secret_free_and_reads_cached_status`
- passed: `PYTHONPATH=src python3 -m compileall -q src tests`

Pending:

- completed: commit `81a77c1b` pushed to `develop`.
- completed: EC2 `git pull --ff-only origin develop`.
- completed: restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`; both `active`.
- completed: EC2 deployed commit `81a77c1b`.
- completed: `stockanalysis-operations ai-agent-registry-report --env-file /opt/stockanalysis/runtime/data-operations.env`
  - `agent_count=13`
  - `default_primary_provider=agents_sdk_openai`
  - `default_fallback_provider=codex_oauth`
  - `default_local_fallback_provider=local_rules`
  - `order_boundary=read_only_no_order`
- completed: `stockanalysis-operations openai-provider-health-report --env-file /opt/stockanalysis/runtime/data-operations.env`
  - `status=openai_insufficient_quota`
  - `fallback_required=true`
  - `fallback_provider=codex_oauth`
  - `local_fallback_provider=local_rules`
- completed: authenticated `/api/data-health`
  - `overall_status=healthy`
  - `open_gates=[]`
  - `live_ai_invocation_health.status=recovered_with_recent_failures`
  - `live_ai_invocation_health.attention_required=false`
  - `openai_provider_health.status=openai_insufficient_quota`
- completed: local tunnel route smoke
  - `http://127.0.0.1:13000/` returned `200`
  - `http://127.0.0.1:13000/data-health` returned `200`

Boundaries:

- No recommendation weight change.
- No AI-driven order decision.
- No broker submit.

Exact next step:

- Continue with `manual-weight-review-pilot-decision-v1`; do not start `manual-weight-review-pilot-v1` until the user explicitly approves the pilot scope and read-only/no-order boundary.
