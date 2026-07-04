# ai-batch-provider-fallback-hardening-v1 Handoff

## 2026-07-04

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

- Commit, push, EC2 pull/restart.
- EC2 smoke:
  - `stockanalysis-operations ai-agent-registry-report --env-file /opt/stockanalysis/runtime/data-operations.env`
  - `stockanalysis-operations openai-provider-health-report --env-file /opt/stockanalysis/runtime/data-operations.env`
  - `/api/data-health` confirms fallback visibility and `open_gates=[]`.

Boundaries:

- No recommendation weight change.
- No AI-driven order decision.
- No broker submit.
