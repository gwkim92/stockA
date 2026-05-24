# Session Handoff

## Current Status

- 완료:
  - `/ai-evidence`에 직접 종목 후보, 상위 흐름 후보, 차단 후보의 차이를 설명하는 읽는 순서 섹션을 추가했다.
  - `/ai-evidence/results`에 직접 종목, 상위 흐름, 뉴스 묶음, 추천 연결 기준을 분리해 표시했다.
  - `/ai-evidence/blocked`에 차단 이유, 복구 가능성, 현재 자동 제외 상태를 추가했다.
  - `사람이 확인`, `태그 검수`, `검토 가능`처럼 실제 기능과 맞지 않는 문구를 제거했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: EC2에 배포해 `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked` route smoke를 확인한다.

## Verification Evidence

- `cd apps/web && npm run typecheck` - passed.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` - passed.
- `git diff --check` - passed.
- `cd apps/web && npm run build` - passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-lane-clarity` - passed.
- EC2 `cd apps/web && npm run build` - passed.
- EC2 `stockanalysis-web.service` restart - active.
- EC2 internal route smoke:
  - `/ai-evidence` contains `뉴스 AI 후보는 세 갈래로 나뉜다`, no server render/digest text.
  - `/ai-evidence/results` contains `구조화 결과 읽는 법`, `거시·테마로 먼저 저장`, `추천에 연결되는 방식`, no server render/digest text.
  - `/ai-evidence/blocked` contains `차단 후보는 이렇게 처리한다`, `자동 제외 상태`, `차단 기록 있음`, no server render/digest text.
- Local SSH tunnel `http://127.0.0.1:13000` route smoke for the same three pages - passed.
