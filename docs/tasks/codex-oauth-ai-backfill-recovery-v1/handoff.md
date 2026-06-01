# codex-oauth-ai-backfill-recovery-v1 Handoff

## Current Status

- status: partially_backfilled_ec2_smoked
- current status: validator false-fail fix is committed/pushed/deployed; controlled EC2 backfill restored a first tranche of missing AI outputs and downstream cycle/research refresh succeeded.
- in progress: 남은 번역/AI 구조화 누락분은 긴 backfill queue로 남아 있으며, batch size를 작게 유지해 반복 처리해야 한다.
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
- commit/push/deploy:
  - local/GitHub commit: `0a0389d Fix news translation grounding for backfill recovery`
  - EC2 app updated to `0a0389d`
- EC2 controlled backfill:
  - translation batch 1 `run_id=2559`: requested 50, updated 48, failed 2
  - news AI extract batch 1 `run_id=2560`: requested 50, inserted artifact 50, failed 0, rejected candidate 0
  - translation batch 2 `run_id=2561`: requested 50, updated 49, failed 1
  - news AI extract batch 2 `run_id=2562`: requested 20, inserted artifact 15, failed 0, rejected candidate 5
  - hierarchical propagation `run_id=2563`: propagated impact 1822, event count 222, instrument count 10
  - cycle hierarchy snapshot `run_id=2564`: node count 18
  - cycle community AI summary `run_id=2566`: inserted summary 10, failed 0
  - equity research reporting `run_id=2567`: inserted artifact 5, failed 0
  - stale direct impact cleanup `run_id=2568`: removed 1 source-ungrounded ZS direct impact
  - quality audit output refreshed at `/opt/stockanalysis/runtime/reports/cycle-ai-quality-audit-latest.json`

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task codex-oauth-ai-backfill-recovery-v1`
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_news_rss_translation -v`
- WARN: EC2 AWH verify was skipped because `/opt/agent-work-harness/src` was not available on the host.
- PASS: EC2 FastAPI/Next services active after deploy.
- PASS: `/api/data-health.live_ai_invocation_health.status=recovered_with_recent_failures`, attention false, latest monitored AI tasks all succeeded.
- PASS: latest quality audit after cleanup: score 85, issue count 1, duplicate title count 1, ungrounded direct ticker 0, macro false ticker 0, quantum-energy mislink 0.

## Remaining

- 남은 누락:
  - 한국어 번역 누락: 183
  - 뉴스 AI 구조화 누락: 461
- 48시간 관찰창에는 과거 실패가 남아 있다. 현재 최신 monitored task는 성공이므로 operational gate는 닫혀 있다.
- 남은 실패 샘플:
  - `ai`, `cockpit`, `cd` 같은 원문 밖 token은 validator가 계속 차단했다. `cockpit`은 prompt leakage 가능성이 있어 저장 금지 유지.
- 남은 품질 이슈:
  - 동일 제목 중복 1건. duplicate cleanup dry-run에서는 downstream 없는 삭제 후보가 0건이라 자동 삭제하지 않았다.
- 전체 queue를 한 번에 밀면 오래 걸리므로 `news-rss-translation-run`은 50건 이하, `news-rss-ai-extract-run`은 20건 이하로 반복 실행하는 것이 안전하다.

## Order Boundary

- 추천 scoring weight 변경 금지.
- broker submit/실거래 활성화 금지.
- benchmark/portfolio position 변경 금지.

## Exact Next Step

- exact next step: continue EC2 controlled backfill in small batches until `translation_missing` and eligible `ai_extract_missing` plateau, then rerun propagation, cycle snapshot, cycle AI quality audit with output refresh, and report the remaining true data-quality blockers separately from OAuth recovery.
