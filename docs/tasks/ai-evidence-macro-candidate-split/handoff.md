# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - `/ai-evidence`를 직접 종목 후보와 상위 흐름 후보 섹션으로 분리했다.
  - `/events` 기본 판단 목록을 직접 종목 후보와 상위 흐름 후보 섹션으로 분리했다.
  - 종목 없는 거시/테마 뉴스가 오류가 아니라 상위 흐름 입력임을 설명하는 문구를 추가했다.
  - EC2에 `855b496`를 배포하고 Next.js를 rebuild/restart했다.
  - 브라우저에서 `/events`, `/ai-evidence`의 직접 종목/상위 흐름 분리를 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/ai-evidence`에서 `symbol`이 `UNKNOWN`/`UNCLASSIFIED`인 후보를 상위 흐름 후보 섹션으로 분리한다.
- `/events` 기본 판단 목록도 직접 종목 후보와 상위 흐름 후보를 분리한다.
- 상위 흐름 후보는 “종목 미분류 오류”가 아니라 “테마/거시 흐름으로 전파될 후보”라는 설명을 붙인다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-macro-candidate-split`
- PASS: EC2 `cd apps/web && npm run build`
- PASS: EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`
- PASS: Browser smoke `http://127.0.0.1:13000/events`
  - shows `직접 종목 후보`
  - shows `상위 흐름 후보`
  - shows `종목을 억지로 붙이지 않는 거시·테마 뉴스`
- PASS: Browser smoke `http://127.0.0.1:13000/ai-evidence`
  - shows `직접 종목 뉴스 후보`
  - shows `종목 없이 먼저 보는 거시·테마 후보`
  - shows `거시·테마 뉴스는 관련 종목군으로 전파되는 상위 입력이다`

## Remaining

- 다음 UI 품질 이슈는 후보 카드 내부의 `개별 AI 후보` 버튼명과 관련 이벤트 설명이 여전히 후보 종류별로 충분히 세분화되지 않았다는 점이다.

## Exact Next Step

- exact next step: continue wording cleanup inside candidate cards and relationship chips, or start the backend quality task that promotes macro-only candidates into propagated recommendation evidence.
