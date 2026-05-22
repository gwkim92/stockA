# Session Handoff

## Current Status

- 상태: ec2_systemd_identity_fix_in_progress
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
  - 2026-05-22 재점검에서 단건 SSH 실행은 성공하지만 `stockanalysis-operating-data-news-intraday.service`는 root로 실행되어 `/root/.codex`를 사용하고, root에는 OAuth `auth.json`이 없어 401이 발생하는 것을 확인했다.
  - 실제 로그인된 OAuth context는 `/home/ec2-user/.codex/auth.json`에 있고, 해당 파일 내용은 출력하지 않았다.
  - `operating-data-profile-scheduler-invocation-plan`에 systemd `User=`, `Group=`, `HOME`, `CODEX_HOME`, `XDG_CONFIG_HOME` manifest 옵션을 추가했다.
  - operating-data profile scheduler의 기본 job name이 `stockanalysis-local-ingest-worker`로 엮여 실제 설치 대상인 `stockanalysis-operating-data-*`와 어긋나는 문제도 함께 수정했다.
- 막힌 점:
  - 과거 실패의 최종 CLI error line은 기존 저장 방식 때문에 복구할 수 없다.
  - 현재 같은 SSH 단건 경로의 1건 smoke는 성공하지만, 설치된 EC2 systemd unit은 아직 `ec2-user` 실행자로 재설치/검증이 필요하다.

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
- FAIL: EC2 `sudo systemctl start stockanalysis-operating-data-news-intraday.service` before identity fix produced run `311`, status `succeeded_with_fallback`, 10 `codex_oauth` invocations, 10 failures. Error tail: `401 Unauthorized: Missing bearer or basic authentication in header`.
- ROOT CAUSE: installed profile scheduler service has no `User=` and runs as root; root has no Codex OAuth `auth.json`, while `/home/ec2-user/.codex/auth.json` exists.
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_operating_data_profile_scheduler -v`
- PASS: `bash scripts/verify_operating_data_profile_scheduler_invocation.sh`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `git diff --check`
- PARTIAL: EC2 first redeploy attempt generated `stockanalysis-local-ingest-worker-*` manifests because of the default job-name mismatch; this is now fixed in code and needs redeploy.

## Remaining

- Commit/push the systemd identity manifest fix.
- Deploy to EC2.
- Regenerate profile scheduler manifests with:
  - `--systemd-user ec2-user`
  - `--systemd-group ec2-user`
  - `--systemd-home /home/ec2-user`
- Install generated `.service` and `.timer` files to `/etc/systemd/system`.
- `systemctl daemon-reload`, restart timers, then manually start `stockanalysis-operating-data-news-intraday.service` once.
- Verify latest `event_intelligence_llm_extract` run has `codex_oauth` succeeded invocations instead of 401 fallback.

## Exact Next Step

- exact next step: deploy the systemd identity manifest fix to EC2 and verify the profile scheduler path uses `ec2-user` Codex OAuth context.
