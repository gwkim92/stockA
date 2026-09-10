# Implemented AI usage

| Workload | Actual invocation adapter | Providers | Model selection |
| --- | --- | --- | --- |
| News Korean translation | `ingest/news/translation.py` | Codex OAuth, OpenAI Agents SDK, fixture/local fallback | Saved Codex setting; SDK registry policy / explicit request |
| News event extraction | `ingest/news/ai_extract.py` | Codex OAuth, OpenAI Agents SDK, fixture/local fallback | Saved Codex setting; SDK registry policy / explicit request |
| SEC event extraction | `ingest/sec/ai_event_extract.py` | Fixture by default, opt-in Codex OAuth | Saved Codex setting when Codex is selected |
| Cycle/community summary | `ai/cycle_community_ai_summary.py` | Codex OAuth, fixture fallback | Saved Codex setting |
| Equity research report | `ai/equity_research_reporting.py` | Codex OAuth, fixture fallback | Saved Codex setting |

Paths are relative to `src/stockanalysis/`. The generic SDK runner is `ai_agents/agents_sdk_provider.py`; only the two news adapters call it. `frontend/codex_oauth_operator.py` has diagnostic calls, not a sixth production analysis workload. Document chunk creation, deterministic local embeddings/rules and fixtures do not call an external model.

The 13 registry entries are role/prompt policies. They are not evidence of 13 independently implemented model consumers. The UI retains them as a collapsed reference and shows live operational workload information separately.

## Model precedence and evidence

For Codex: an explicit per-run model wins; otherwise workload override, then the saved shared default, then the legacy CLI command when no settings store is configured. `codex-cli-default` is an application sentinel meaning defer to CLI configuration, not an OpenAI model identifier.

The server's existing CLI command pins `gpt-5.6-terra`; the new store is initialized to the same model. Saved selections append `--model` at invocation time. They do not switch providers, change reasoning settings, start analysis, or rewrite OAuth/config files.

The settings API shows the latest business DB invocation (provider, recorded model, status, timestamp). Legacy placeholder model records remain explicitly labelled as recorded values. New sanitized runtime observations record requested model, selected model, CLI-observed model, CLI reasoning header, start/end, settings revision and provider-adapter success/failure. CLI selection is not proof of provider-side internal routing or downstream business acceptance. The separate business invocation record supplies the latter pipeline status.

## Security and operations

SQLite file: `STOCKANALYSIS_AI_MODEL_SETTINGS_PATH`, shared by API and batch service envs, outside the checkout. New files have mode 0600. SQL is parameterized; revision checks, setting writes and audit insertion use a single immediate transaction. The business Postgres schema is unchanged.

Initialize once with `python -m stockanalysis.ai.model_settings init --default-model gpt-5.6-terra`, then `refresh-catalog`. The catalog comes from authenticated `codex app-server` `model/list`, excludes hidden entries, and has a visible observation timestamp. Catalog refresh does not invoke a model.

Issue a one-use, 10-minute access code with `grant-access` under the server's operational environment. Redeeming it creates a 30-day model-manager session; both code and session are stored only as SHA-256 digests. The browser receives only an HttpOnly SameSite=Strict cookie scoped to the model settings route. Production HTTPS sets Secure; local SSH tunnel HTTP is supported. Public HTTP writes and cross-origin writes are rejected. Logout revokes the session server-side. Ordinary frontend read-token access cannot change settings. The existing broader admin-action token is never used by the new browser bridge.

GET inventory and PATCH settings use `/__admin/model-settings`; session creation/deletion use `/__admin/model-settings/session`. Every backend route also requires the existing read bearer boundary. Next same-origin routes are `/api/ai-model-settings` and `/api/ai-model-settings/session`. Request bodies are bounded and error output excludes stack traces, paths and credentials.
