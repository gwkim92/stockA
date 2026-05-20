# Review Notes

- Implemented `codex_oauth` without reading `~/.codex/auth.json`.
- OAuth usage is isolated to `codex exec`; structured output is persisted through the existing AI metadata tables.
- The adapter first failed because Codex CLI global options and strict schema requirements differed from initial assumptions; both were corrected and covered by tests.
- Real smoke persisted one successful `ai.model_invocation` row with provider `codex_oauth`.
