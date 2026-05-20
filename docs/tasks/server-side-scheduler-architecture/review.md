# Review

## Review Notes

- Mac `LaunchAgents`를 최종 운영 경로로 보이게 만들던 문서/화면 표현을 서버형 scheduler + worker 구조로 재정렬했다.
- `/data-health`는 최근 단발 실행 성공과 반복 scheduler 미배포를 분리해서 설명한다.
- 실제 `launchctl`, LaunchAgents write/delete, scheduler installation은 수행하지 않았다.
- 후속 결정으로 server scheduler deployment target 선택은 future option으로 내려갔다. immediate work는 `local-first-runtime-direction`이다.

## Verification Evidence

- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- Browser smoke: `http://127.0.0.1:3001/data-health`, title `데이터 수집 | 스톡애널리시스 대시보드`, required text checks true, raw "수동 승인 대기" wording absent, console error count 0.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task server-side-scheduler-architecture`: pass.
- `git diff --check`: pass.
