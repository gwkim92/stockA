# Frontend Domain Language Normalization Plan

## Goal

- 화면에 노출되는 내부 코드 표현을 사용자가 이해할 수 있는 한국어 운영 문구로 정리한다.
- 특히 `avoid`, `exclude`, `long_term_core`, `ANNUAL_REPORTING`, `forming`, `unavailable`, `recommendation score falls below 0.3500`처럼 문장 안에 섞여 남는 raw code를 줄인다.

## Scope

- 공통 label/wording helper를 개선한다.
- thesis/recommendation 화면의 명백한 raw badge/version 표기를 정리한다.
- API contract, DB schema, scoring, recommendation action rule, LLM/RAG, broker/order, scheduler는 변경하지 않는다.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- live browser smoke for `/theses/AAPL-bootstrap-v1`
- live browser smoke for `/recommendations/AAPL-2024-11-01`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-domain-language-normalization`
- `git diff --check`
