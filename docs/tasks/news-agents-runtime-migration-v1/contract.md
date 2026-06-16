# news-agents-runtime-migration-v1 Contract

## Task Request

- request: 뉴스 번역과 뉴스 구조화 runner를 새 AI agent registry/runtime boundary 뒤로 이동한다.
- context: `ai-agent-registry-foundation-v1`에서 agent catalog, prompt version, model policy, safety boundary를 추가했다. 기존 runner는 아직 `fixture`/`codex_oauth` provider 문자열과 하드코딩 prompt에 직접 의존한다.

## Goal

- goal: 뉴스 translation/extract runner가 agent key와 model policy를 report/config/model invocation metadata에 반영할 수 있게 한다.
- goal: 기존 `codex_oauth`와 fixture 테스트 경로는 유지하고, 다음 Agents SDK provider migration이 들어갈 seam을 만든다.
- goal: 추천 weight, scheduler cadence, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/news-agents-runtime-migration-v1/*`
  - `src/stockanalysis/ai_agents/*`
  - `src/stockanalysis/ingest/news/translation.py`
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `tests/test_news_rss_translation.py`
  - `tests/test_news_rss_ai_extract.py`

## Non-Goals

- Do not call OpenAI API or install runtime credentials in this task.
- Do not replace Codex OAuth with Agents SDK in production yet.
- Do not change canonical validator acceptance thresholds.
- Do not change recommendation scoring weights, portfolio positions, scheduler cadence, or broker/order flow.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_ai_agent_registry tests.test_news_rss_translation tests.test_news_rss_ai_extract`
- verification command: `/opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-agents-runtime-migration-v1`
