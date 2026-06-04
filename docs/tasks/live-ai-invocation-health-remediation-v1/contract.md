# live-ai-invocation-health-remediation-v1 Contract

## Task Request

- request: EC2 `/api/data-health`의 `live_ai_invocation_health_attention` gate를 닫는다. 최신 실패 작업은 `news-rss-korean-translation`이며, 실패 원인은 Codex OAuth 로그인 문제가 아니라 번역 모델이 원문에 없는 `AI` 같은 라틴 토큰을 추가해 validator가 차단한 것이다.

## Objective

Close the EC2 `live_ai_invocation_health_attention` gate by fixing the root cause of repeated `news-rss-korean-translation` failures without weakening the validator or hiding failed model output.

## Concrete Goal

- goal: The latest critical AI task execution on EC2 must become successful after a real Codex OAuth Korean translation smoke run, while invalid model output remains rejected and auditable.

## Root Cause

The latest failed document was `ingest.source_document.document_id=15052`.

- Source title: `Nvidia CEO Jensen Huang Is Building the Future Faster Than Infrastructure Can Support It`
- Source summary: empty
- Failure: `news translation output contains ungrounded latin token(s) for document_id=15052: ai`

The Codex OAuth runtime was reachable. The failure was caused by the translation prompt asking for why the item matters, which allowed the model to infer `AI` from the Nvidia context even though the bounded RSS text did not explicitly contain `AI`.

## Scope

- Harden the Korean RSS translation prompt so it behaves as a strict translation step, not an analysis step.
- Keep validator enforcement: unsupported English tokens and inferred concepts must still be rejected.
- Add one strict retry for Codex OAuth translation when validation rejects unsupported Latin tokens.
- Keep model invocation audit history. Failed output is not deleted.
- Do not change recommendation scoring, benchmark, portfolio positions, schema, or broker/order boundaries.

## Mutable Surface

- mutable surface: `src/stockanalysis/ingest/news/translation.py`
- mutable surface: `tests/test_news_rss_translation.py`
- mutable surface: `docs/tasks/live-ai-invocation-health-remediation-v1/`

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src/stockanalysis/ingest/news/translation.py tests/test_news_rss_translation.py`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task live-ai-invocation-health-remediation-v1`
- EC2 smoke:
  - Run `stockanalysis-operations news-rss-translation-run --provider codex_oauth --execute`.
  - Verify latest `news-rss-korean-translation` invocation is `succeeded`.
  - Verify `/api/data-health.open_gates` no longer includes `live_ai_invocation_health_attention`.
