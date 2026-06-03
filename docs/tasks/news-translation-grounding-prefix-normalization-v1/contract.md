# news-translation-grounding-prefix-normalization-v1 Contract

## Task Request

- request: 실제 Codex OAuth 뉴스 번역 배치에서 `overcrowded` 원문이 `crowded` 출력으로 바뀌어 실패한 false positive를 줄인다.
- context: EC2 `live_ai_invocation_health`는 최신 실행은 성공했지만 최근 48시간에 `news-rss-korean-translation` 실패 17건을 기록했다. 최신 실패 예시는 `document_id=14789`의 `crowded` token grounding failure다.

## Goal

- goal: 번역 validator가 원문에 있는 복합/접두 영어 단어의 좁은 파생형은 허용하되, 원문에 없는 회사명, ticker, 제품명, 정책명 환각은 계속 차단한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ingest/news/translation.py`
  - `tests/test_news_rss_translation.py`
  - `docs/tasks/news-translation-grounding-prefix-normalization-v1/*`

## Invariants

- Do not disable grounding validation.
- Do not allow ungrounded company names, ticker symbols, products, policy names, or themes.
- Do not call LLM from FastAPI or Next request path.
- Do not change recommendation scoring weights, benchmark definitions, portfolio positions, broker/order flow, or live trading boundary.
- Do not expose OAuth tokens, read tokens, DB URLs, webhook URLs, or repo-outside paths.

## Scope

- Add a narrow allowed-token normalization for known source-grounded prefix forms such as `overcrowded -> crowded`.
- Add unit regression coverage for the `overcrowded` translation failure.
- Keep broad contamination rejection unchanged.
- EC2 smoke should confirm current services remain active and translation route/tooling still passes tests.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-translation-grounding-prefix-normalization-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] `overcrowded` source text permits `crowded` in Korean translation output.
- [x] Existing ungrounded entity rejection remains covered.
- [x] Local verification passes.
- [ ] EC2 smoke passes without service disruption.
