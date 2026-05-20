# Scheduler Activation Readiness Dashboard Plan

## Summary
- `/data-health`에서 scheduler가 실제 반복 실행 상태인지, 왜 아직 켜지지 않았는지, 다음 사람이 무엇을 해야 하는지 명확히 보여준다.
- 기존 data-health DTO의 scheduler activation fields만 사용한다.
- host LaunchAgent 설치, `launchctl`, repo-outside env 변경은 하지 않는다.

## Scope
- `apps/web/src/app/data-health/page.tsx`에 scheduler activation decision summary를 추가한다.
- task contract/handoff/review를 남긴다.

## Non-Goals
- scheduler 실제 활성화
- launchd plist 설치/삭제/수정
- env/secrets 변경
- backend DTO/schema 변경
- trading/order 동작 변경

## Verification
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/data-health`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task scheduler-activation-readiness-dashboard`
- `git diff --check`
