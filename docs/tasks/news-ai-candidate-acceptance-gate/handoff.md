# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - EC2 실제 데이터에서 accepted `news_event_candidate` artifact 중 저신뢰 무종목 일반 뉴스가 남아 있음을 확인했다.
  - `news-rss-ai-extract-run`이 검증된 theme/instrument impact가 없는 AI output을 accepted `news_event_candidate`가 아니라 `news_event_candidate_rejected`로 저장하게 했다.
  - 기존 rejected artifact도 request hash 중복 조회에 포함해 같은 후보가 반복 LLM 호출되지 않게 했다.
  - no-symbol MarketWatch topstories와 no-symbol broad-theme Yahoo Finance 후보를 pre-AI 후보 선택에서 제외했다.
  - 후보 화면 품질 필터를 확장해 기존 accepted artifact 중 신뢰도 65% 미만인 후보도 기본 candidate 화면에서 숨기게 했다.
  - EC2에서 `codex_oauth` execute가 `Not inside a trusted directory`로 실패하는 원인을 확인했고, Codex CLI batch 호출이 repo workdir과 `--skip-git-repo-check`를 사용하게 보강했다.
  - EC2에 최신 커밋을 배포했고 FastAPI/Next 서비스가 active 상태임을 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- 검증된 theme/instrument impact가 없는 AI output은 accepted `news_event_candidate`가 아니라 `news_event_candidate_rejected`로 저장한다.
- rejected artifact도 request hash 중복 조회에 포함해 같은 후보를 반복 호출하지 않게 한다.
- frontend event list의 candidate 품질 필터를 기존 MarketWatch 무종목 후보에서 일반 뉴스 source의 무종목·저신뢰 후보와 과거 저신뢰 accepted 후보까지 확장한다.
- Codex OAuth batch 호출은 systemd/SSH cwd에 의존하지 않고 repo root workdir을 사용하며, read-only batch 실행을 위해 git repo trust check를 명시적으로 넘긴다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `PYTHONPATH=src /private/tmp/stockanalysis-test-venv/bin/python -m unittest discover -s tests` ran 739 tests.
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-candidate-acceptance-gate`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `eb1ce0f`; focused backend tests and Next build passed; FastAPI/web active.
- PASS: EC2 dry-run `news-rss-ai-extract-run --as-of-date 2026-05-22 --provider codex_oauth --limit 20 --dry-run` returned `planned` with 20 candidates and no writes.
- PASS: EC2 execute after Codex workdir fix returned run `304`, status `completed`, `failed_candidate_count=0`, `rejected_candidate_count=1`, artifact `117`, invocation `308`, status `rejected_no_validated_impacts`.
- PASS: EC2 `/api/events?evidenceType=news_event_candidate` returned visible candidate count `11`, suppressed low-signal count `16`, and `low_confidence_visible=0`.
- PASS: EC2 DB artifact count showed accepted `news_event_candidate=46`, rejected `news_event_candidate_rejected=1`.
- PASS: EC2 `/api/data-health` showed AI latest run `pipeline-run-304`, `latest_status=succeeded`, `health_status=ok`.
- PASS: Browser smoke `http://127.0.0.1:13000/ai-evidence` showed `뉴스 AI 근거`, `품질 필터 숨김 16`, `직접 종목 뉴스 후보`, `상위 흐름 후보`; low-confidence old INTU/ELF candidates were not visible, while high-confidence NVDA stayed visible.
- PASS: Browser smoke `http://127.0.0.1:13000/data-health` had no load error or AI fallback warning and still showed EC2 scheduler/news flow sections.

## Remaining

- 없음.

## Exact Next Step

- exact next step: continue with recommendation/holding-review traceability so accepted news and macro-flow evidence show exactly where they affected recommendations and portfolio review.
