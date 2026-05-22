# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - `/events`에서 news candidate 링크와 상태 설명을 `종목 AI 근거` / `흐름 AI 근거`로 분리했다.
  - `/events`에서 상위 흐름 후보의 관련 이벤트 empty text를 별도로 작성했다.
  - `/ai-evidence` 카드의 상세 버튼을 `종목 근거 상세` / `흐름 근거 상세`로 분리했다.
  - `/ai-evidence` 상단 badge를 `뉴스 AI 근거`로 정리했다.
  - EC2에 `1bcf7b0`를 배포하고 Next.js를 rebuild/restart했다.
  - 브라우저에서 `/events`, `/ai-evidence`의 후보 종류별 문구를 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/events`의 evidence label/detail/purpose 문구를 후보 종류별로 나눈다.
- `/ai-evidence`의 카드 badge와 상세 버튼명을 후보 종류별로 나눈다.
- 관련 이벤트가 없는 경우 직접 종목 후보와 상위 흐름 후보를 다르게 설명한다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task candidate-card-wording-cleanup`
- PASS: EC2 `cd apps/web && npm run build`
- PASS: EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`
- PASS: Browser smoke `http://127.0.0.1:13000/events`
  - shows `종목 AI 근거`
  - shows `흐름 AI 근거`
  - shows `아직 이 상위 흐름에서 전파된 종목 근거나 강한 관련 이벤트가 연결되지 않았다`
  - shows `AI가 이 뉴스를 거시·테마 흐름으로 구조화했다`
- PASS: Browser smoke `http://127.0.0.1:13000/ai-evidence`
  - shows `뉴스 AI 근거`
  - shows `종목 근거 상세`
  - shows `흐름 근거 상세`
  - shows `추천 판단에 들어가기 전 확인할 근거 경로`

## Remaining

- 다음 범위는 상위 흐름 후보가 실제 추천/보유검토 근거에서 어떻게 쓰였는지 더 직접적으로 추적하게 만드는 것이다.

## Exact Next Step

- exact next step: inspect macro-flow propagation and recommendation detail evidence path, then expose any missing trace from upper-flow candidate to recommendation input.
