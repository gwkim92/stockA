# Session Handoff

## Active Task

- 이름: operating-cockpit-information-architecture
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - 홈/헤더/분석 화면을 daily operating flow 기준으로 재정렬한다.
  - 기존 `news_event_candidate` artifact가 새 한국어 prompt template version 재실행을 막지 않도록 후보 선택 SQL을 보강한다.
- 진행 중:
  - EC2 배포와 실제 AI 후보 재생성 smoke가 남아 있다.

## Exact Next Step

- exact next step: `apps/web` 타입/빌드 검증 후 EC2에 배포하고, 새 한국어 prompt version으로 `news-rss-ai-extract-run` dry-run/execute를 수행해 기존 영어 AI 후보가 재생성되는지 확인한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract`: pass.
- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task operating-cockpit-information-architecture`: pass.

## Risks

- 이번 task는 UX 정보 구조와 AI 후보 재생성 boundary 작업이다. 추천 품질 산식, broker/order flow, DB schema는 바꾸지 않는다.
