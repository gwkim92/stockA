# codex-oauth-ai-backfill-recovery-v1 Handoff

## Current Status

- status: in_progress
- current status: validator false-fail fix implemented locally; EC2 backfill not run yet.
- in progress: Codex OAuth 장애 기간의 누락 AI 분석을 backfill하기 위한 recovery task를 시작했다.
- 기준일: 2026-06-01

## Root Cause

- EC2 Codex OAuth 인증이 `token_invalidated`/`refresh_token_reused`/`401 Unauthorized` 상태가 되어 실제 LLM batch가 실패했다.
- 이후 재로그인으로 실제 Codex OAuth 호출은 복구됐다.
- 복구 직후 일부 번역 실패는 OAuth 문제가 아니라 번역 grounding validator가 `yahoo-finance-news`, `finance.yahoo.com`, `marketwatch.com`, `crypto-linked`, `ETFs` 같은 원천 기반 복합 토큰을 단일 토큰으로만 비교해 false-fail시킨 문제였다.

## Impact Found So Far

- 최근 72시간 기준 `ai.model_invocation`에서 확인한 장애 영향:
  - `news-rss-korean-translation`: failed 708, succeeded 34
  - `news-rss-ai-extract`: failed 350, succeeded 17
  - `cycle-community-ai-summary-v2`: failed 12, succeeded 1
  - `ai-equity-research-reporting`: failed 5, succeeded 1
- 최신 누락 후보:
  - 한국어 번역 누락: 280
  - 뉴스 AI 구조화 누락: 530

## Implemented

- task contract를 추가했다.
- 번역 grounding validator가 원천 메타데이터의 복합 token을 분해해 허용하도록 보정했다.
  - 예: `yahoo-finance-news` -> `yahoo`, `finance`
  - 예: `finance.yahoo.com` -> `finance`, `yahoo`
  - 예: `crypto-linked` -> `crypto`
  - 예: `etfs` -> `etf`
- 원문에 없는 `SpaceX/Starlink` 같은 고유명사 차단 테스트는 유지했다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation -v`

## Remaining

- 전체 local verification을 실행한다.
- patch를 commit/push/deploy한다.
- EC2에서 제한 배치 backfill을 실행한다.
- backfill 이후 남은 실패가 OAuth 장애인지 데이터 품질 차단인지 재분류한다.
- downstream propagation, cycle snapshot, AI summary/research 연결 상태를 확인한다.

## Order Boundary

- 추천 scoring weight 변경 금지.
- broker submit/실거래 활성화 금지.
- benchmark/portfolio position 변경 금지.

## Exact Next Step

- exact next step: commit/push/deploy the translation validator patch, then run EC2 controlled backfill batches for `news-rss-korean-translation` and `news-rss-ai-extract` before downstream propagation/cycle/research refresh.
