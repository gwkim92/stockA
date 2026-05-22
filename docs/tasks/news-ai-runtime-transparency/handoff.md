# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - EC2 데이터에서 뉴스 수집/분석 상태를 확인했다.
  - 확인 결과:
    - `news_rss_item` 이벤트 170건.
    - `news_event_candidate` Codex OAuth 성공 artifact 43건.
    - 최신 `news_cluster_summary`는 `local_rules` 기반 artifact 70건.
    - 최근 Codex OAuth 뉴스 후보 배치들은 실패 invocation을 남겼다.
  - `/api/ai/news-clusters` summary에 LLM 후보 invocation/artifact 통계를 추가했다.
  - `/intelligence`에서 LLM 후보 분석, 로컬 규칙 뉴스 묶음, 영어 원문/키워드가 남는 이유를 분리 표시했다.
  - EC2에 배포하고 실제 API/브라우저로 검증했다.
- 막힌 점:
  - 없음. 단, Codex OAuth 실패 원인 복구는 이번 task 범위가 아니라 별도 provider/runtime fix로 다룬다.

## Planned Fix

- `/api/ai/news-clusters` summary에 LLM 후보 분석 성공/실패 수를 추가한다.
- `/intelligence`에서 “LLM 후보 분석”과 “로컬 규칙 뉴스 묶음”을 분리해서 표시한다.
- 영어 원문/키워드가 남는 이유를 화면에 설명한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-runtime-transparency`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `99d1d30`; backend test and Next build passed; `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- PASS: EC2 API smoke `/api/ai/news-clusters?limit=4` returned `cluster_count=12`, `local_rule_cluster_count=12`, `llm_candidate_artifact_count=43`, `llm_candidate_success_count=43`, `llm_candidate_failed_count=189`, `latest_llm_invocation_status=failed`, `latest_llm_provider=codex_oauth`.
- PASS: Browser smoke `http://127.0.0.1:13000/intelligence` showed `LLM 후보 분석`, `최근 LLM 실패`, `성공 artifact 43건`, `실패 호출 189건`, `뉴스 묶음 방식`, `규칙 기반`, `로컬 규칙 묶음`, and the language policy section.

## Remaining

- 없음.

## Exact Next Step

- exact next step: investigate and fix the Codex OAuth runtime failure so latest news candidate LLM extraction succeeds again, or intentionally downgrade the job label from AI to rule-based when OAuth is unavailable.
