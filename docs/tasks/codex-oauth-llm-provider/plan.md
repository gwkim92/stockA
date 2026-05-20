# Implementation Plan

## Steps

- Add `codex_oauth` as a provider option for SEC event intelligence extraction.
- Keep fixture mode unchanged and require `--llm-output-json` only for fixture mode.
- Invoke `codex exec` with `read-only`, `never`, `ephemeral`, and structured output schema.
- Validate runtime readiness with `STOCKANALYSIS_LLM_PROVIDER=codex_oauth` and `STOCKANALYSIS_CODEX_CLI_COMMAND`.
- Run unit tests and one real local Codex OAuth smoke against the existing SEC filing artifact.

## Safety Rules

- Do not read or copy Codex OAuth token files.
- Do not use Codex OAuth token as OpenAI API Bearer token.
- Do not call LLM from FastAPI read routes.
