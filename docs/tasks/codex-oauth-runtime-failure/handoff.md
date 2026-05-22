# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - 이전 task에서 확인한 EC2 상태:
    - `news_event_candidate` Codex OAuth 성공 artifact 43건.
    - 최근 Codex OAuth 뉴스 후보 invocation은 실패.
    - `/api/ai/news-clusters` summary 기준 `llm_candidate_failed_count=189`, `latest_llm_invocation_status=failed`.
  - EC2 최소 `codex exec` + JSON schema smoke는 성공했다.
  - EC2 실제 `news-rss-ai-extract-run --env-file /opt/stockanalysis/runtime/data-operations.env --limit 1 --execute`는 성공했다.
  - 잘못된 `frontend-api.env`로 operations runner를 실행하면 `STOCKANALYSIS_PSQL_COMMAND`가 없어 실패한다는 점을 확인했다.
  - 자동 `news-intraday` 서비스는 올바른 `data-operations.env`를 사용하지만, 2026-05-21 22:33 UTC의 `news-ai-evidence` 단계는 10건 모두 `failed_fallback_rules`였고 전체 service는 fallback 정책 때문에 성공 처리됐다.
  - 과거 실패의 정확한 마지막 에러는 기존 코드가 stderr 앞 2000자만 저장해서 DB에서 잘린 상태였다.
  - Codex 실패 기록이 앞으로는 prompt 앞부분이 아니라 diagnostic tail을 보존하도록 수정했다.
  - 수정 배포 후 실제 `codex_oauth` 뉴스 후보 1건 smoke가 성공했다.
- 막힌 점:
  - 과거 실패의 최종 CLI error line은 기존 저장 방식 때문에 복구할 수 없다. 현재 같은 경로의 1건 smoke는 성공한다.

## Investigation Plan

- EC2에서 secret을 출력하지 않고 Codex CLI 위치/버전/관련 env 존재 여부를 확인한다.
- 최소 `codex exec` + JSON schema 호출을 재현한다.
- 실제 `invoke_codex_oauth_news_ai_provider()`가 만드는 명령과 최소 재현의 차이를 비교한다.
- 코드 수정이 가능한 원인이면 focused test 후 수정한다.

## Verification Log

- PASS: EC2 Codex CLI diagnostics: `codex-cli 0.132.0`, auth file exists, minimal `codex exec` schema smoke succeeded.
- PASS: EC2 actual news AI smoke: run `299`, event `55`, artifact `114`, invocation `303`, validated theme `1`, validated instrument `1`.
- PASS: EC2 scheduler inspection: `stockanalysis-operating-data-news-intraday.service` uses `/opt/stockanalysis/runtime/data-operations.env`.
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task codex-oauth-runtime-failure`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `12530a9`; `tests.test_news_rss_ai_extract` and `compileall` passed.
- PASS: EC2 post-deploy `news-rss-ai-extract-run --as-of-date 2026-05-22 --limit 1 --provider codex_oauth --execute` returned run `300`, event `107`, artifact `115`, invocation `304`, `inserted_validated`, validated theme `1`, validated instrument `1`.
- PASS: EC2 API summary `/api/ai/news-clusters?limit=1` returned `llm_candidate_artifact_count=45`, `llm_candidate_success_count=45`, `llm_candidate_failed_count=189`, `latest_llm_invocation_status=succeeded`, `latest_llm_provider=codex_oauth`.

## Remaining

- 없음.

## Exact Next Step

- exact next step: decide whether `completed_with_fallback` should remain a successful scheduler outcome or become a degraded/warning status in `/data-health`.
