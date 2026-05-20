# News Operation Flow Disclosure Plan

## Goal

- `/intelligence` 화면에서 뉴스가 언제, 얼마마다, 어떻게 수집되고 분석되며 프로젝트 어디에 쓰이는지 바로 이해할 수 있게 만든다.

## Scope

- 포함:
  - 기존 `data-health` DTO를 `/intelligence`에서 함께 읽는다.
  - `news-rss-daily` 최신 실행 상태와 scheduler activation 상태를 표시한다.
  - 뉴스 운영 단계: 수집, 정규화, 분석, 사용처, 자동화 상태를 한국어로 설명한다.
  - task docs와 verification evidence를 남긴다.
- 제외:
  - DB schema 변경
  - RSS feed URL 추가/수정
  - scheduler host activation
  - live LLM/RAG 호출
  - recommendation scoring 변경
  - broker/order/write flow

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/intelligence`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-operation-flow-disclosure`
- `git diff --check`
