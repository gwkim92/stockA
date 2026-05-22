# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - 이전 조사에서 자동 `news-intraday` 서비스가 fallback 정책 때문에 systemd 성공으로 끝나지만, `news-ai-evidence` 단계는 `completed_with_fallback`일 수 있음을 확인했다.
  - `run_news_rss_ai_extract()`가 후보 실패를 fallback 처리한 경우 `ops.pipeline_run.status='succeeded_with_fallback'`으로 저장하게 했다.
  - `/api/data-health` SQL이 `succeeded_with_fallback`을 `health_status='degraded'`로 매핑하게 했다.
  - `/data-health`에 AI fallback 경고 영역과 한국어 라벨을 추가했다.
  - EC2에 배포하고 의도적 fallback smoke, 브라우저 경고 표시, 정상 Codex 복구 smoke를 검증했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `run_news_rss_ai_extract()`가 실패 후보를 fallback 처리한 경우 pipeline run status를 `succeeded_with_fallback`으로 저장한다.
- `/api/data-health`는 해당 status를 `degraded`로 매핑한다.
- `/data-health`는 AI 분석 카드에서 fallback 상태를 경고 문구로 표시한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-ai-fallback-degraded`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `c12cddd`; focused backend tests, compileall, Next build passed; FastAPI/web active.
- PASS: EC2 intentional fallback smoke with invalid model returned run `301`, `status=completed_with_fallback`, `failed=1`.
- PASS: EC2 `/api/data-health` after fallback returned AI run `pipeline-run-301`, `latest_status=succeeded_with_fallback`, `health_status=degraded`.
- PASS: Browser smoke `http://127.0.0.1:13000/data-health` showed `AI 분석 경고`, `뉴스 AI 분석이 fallback으로 끝난 실행이 있다`, `성공했지만 fallback 사용`, and `품질 저하`.
- PASS: EC2 normal Codex restore smoke returned run `302`, event `253`, artifact `116`, invocation `306`, `inserted_validated`, `failed=0`.
- PASS: EC2 `/api/data-health` after restore returned AI run `pipeline-run-302`, `latest_status=succeeded`, `health_status=ok`.

## Remaining

- 없음.

## Exact Next Step

- exact next step: continue with UI/data quality cleanup now that AI fallback is visible and latest Codex OAuth status is healthy again.
