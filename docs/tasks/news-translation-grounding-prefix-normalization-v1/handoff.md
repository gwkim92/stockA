# news-translation-grounding-prefix-normalization-v1 Handoff

## Current Status

- 진행 중: implementation and local verification passed; AWH and EC2 smoke pending.
- 시작: 2026-06-03

## Context

- EC2 data-health is currently healthy with open gates `[]`.
- `live_ai_invocation_health` is `recovered_with_recent_failures`: latest monitored AI tasks are succeeding, but recent historical translation failures remain in the 48-hour window.
- The latest visible failure cited `news translation output contains ungrounded latin token(s) for document_id=14789: crowded`.
- Direct DB inspection showed document `14789` title contains `overcrowded`, and a later run already wrote Korean translation successfully.

## Scope

- Tighten validator normalization only for source-grounded prefix-derived English tokens.
- Do not loosen company/ticker/product hallucination guards.
- Do not change scoring, portfolio, benchmark, scheduler cadence, broker/order boundary, or request-time AI behavior.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`

## Next Step

- exact next step: run AWH verify, commit/push, deploy to EC2, and run EC2 targeted translation tests plus service smoke.
