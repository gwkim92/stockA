# news-intraday-runtime-recovery-observation-v1 Contract

## Task Request

- request: 번역 grounding 보강 이후 EC2 `news-intraday` 자동 실행이 실제로 복구됐는지 확인하고 증거를 남긴다.
- context: 직전 작업은 `overcrowded -> crowded` 번역 grounding false positive를 좁게 허용했다. 사용자는 자동 수집·AI 분석이 실제로 잘 도는지 계속 확인하라고 했다.

## Goal

- goal: EC2 systemd timer, profile run, translation/AI/eval/propagation 결과, data-health 상태를 확인해 현재 자동 뉴스·AI 루프가 정상인지 판단한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/news-intraday-runtime-recovery-observation-v1/*`

## Invariants

- Do not change scheduler cadence or systemd unit files.
- Do not change recommendation scoring weights, benchmark definitions, portfolio positions, broker/order flow, or live trading boundary.
- Do not call extra LLM work beyond the already scheduled EC2 timer run.
- Do not expose DB URL, bearer token, OAuth token, webhook URL, or repo-outside secret file content.

## Scope

- Inspect current EC2 services and timers.
- Observe the latest scheduled `news-intraday` profile result.
- Confirm latest `news-rss-korean-translation` invocations after the fix are successful.
- Confirm `/api/data-health` remains healthy and open gates remain empty.
- Record evidence and next action.

## Verification

- verification command: `systemctl status stockanalysis-operating-data-news-intraday.service`
- verification command: `systemctl list-timers --all stockanalysis-operating-data-news-intraday.timer`
- verification command: read `/opt/stockanalysis/runtime/operating-data-profile-scheduler-reports/news-intraday-operating-data-run.json`
- verification command: authenticated EC2 `/api/data-health` smoke
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-intraday-runtime-recovery-observation-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] Latest scheduled `news-intraday` service completed with systemd success.
- [x] Next `news-intraday` timer run is scheduled.
- [x] Translation step succeeded with `failed_document_count=0`.
- [x] News AI/eval/propagation steps succeeded.
- [x] Data-health remains healthy with open gates empty.
- [x] Handoff records that historical `live_ai_invocation_health.recent_failed_count` is rolling-window history, not a new failure after the fix.
