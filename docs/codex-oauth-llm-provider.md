# Codex OAuth LLM Provider

This provider lets local data operations jobs use the existing Codex ChatGPT login without an `OPENAI_API_KEY`.

The repository does not read, copy, or parse Codex OAuth token files. It calls `codex exec` as a local subprocess and stores only the structured model output and metadata.

## Runtime Env

- `STOCKANALYSIS_LLM_PROVIDER=codex_oauth`
- `STOCKANALYSIS_CODEX_CLI_COMMAND=codex`
- `STOCKANALYSIS_CODEX_TIMEOUT_SECONDS=300`

## Boundary

- Suitable for offline data operations jobs.
- Not suitable for synchronous FastAPI read routes.
- Not a replacement for official OpenAI API key authentication.
- Current CLI compatibility: the provider sets `approval_policy="never"` via `codex exec -c ...` and keeps `--sandbox read-only`, `--ephemeral`, `--ignore-user-config`, and `--ignore-rules`.
