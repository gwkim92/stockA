# Session Handoff

## Current Status

- current status: completed
- 완료: EC2 접근 복구, 최신 코드 배포, EC2 Codex OAuth 재로그인, 실제 `codex_oauth` LLM batch smoke를 완료했다.
- 대상 EC2: `stockanalysis-mvp-20260520` / `i-029d51b163fb07b61`
- 현재 public IPv4: `34.206.72.213`
- EC2 최신 commit: `c1a83d7 fix: require cycle community usage output`
- FastAPI/Next.js systemd services: `active`

## What Changed

- EC2 `ec2-user`에서 `codex login --device-auth`를 완료했다.
- `cycle-community-ai-summary-v2` Codex structured output schema를 최신 strict schema 요구사항에 맞췄다.
  - `usage.additionalProperties=false`
  - `usage.required`에 모든 usage property 추가
  - top-level `required`에 `usage` 추가
- cycle summary provider 실패 진단은 prompt head가 아니라 실제 오류 tail을 보존하도록 변경했다.

## Verification Evidence

- EC2 로그인:
  - `codex login --device-auth`
  - 결과: `Successfully logged in`
- EC2 배포:
  - `git pull --ff-only origin codex/local-mvp-runtime-aws-bootstrap`
  - 결과 commit: `c1a83d7`
- EC2 검증:
  - `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
  - `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_cycle_community_ai_summary`
  - 결과: `Ran 7 tests ... OK`
- EC2 서비스:
  - `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service`
  - 결과: `active`, `active`
- 실제 LLM smoke:
  - 명령: `stockanalysis-operations cycle-community-ai-summary-v2-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-05-25 --node-code TECH_DOMAIN --limit 1 --max-nodes 1 --provider codex_oauth --reasoning-effort low --execute`
  - 결과: `status=completed`
  - `run_id=712`
  - `invocation_id=983`
  - `failed_summary_count=0`

## Root Cause Resolved

- 원래 blocker는 EC2 Codex OAuth token invalidation이었다.
- 재로그인 후에도 `cycle-community-ai-summary-v2`가 실패한 추가 원인은 OpenAI/Codex structured output strict schema 요구사항 불일치였다.
- 최신 실패 원인들은 순서대로 아래와 같았다.
  - `usage.additionalProperties`가 `false`가 아니어서 400 `invalid_json_schema`
  - `usage.required`에 모든 property가 없어서 400 `invalid_json_schema`
  - top-level `required`에 `usage`가 없어서 400 `invalid_json_schema`
- 위 schema 조건을 반영한 뒤 실제 Codex OAuth invocation이 성공했다.

## Remaining Notes

- fallback-only 결과를 성공으로 간주하지 않는 기준을 유지한다.
- Codex OAuth는 계속 offline batch에서만 사용한다. FastAPI request 중 실시간 LLM 호출은 하지 않는다.
- 추천 scoring weight와 실거래 broker submit은 이번 작업에서 바꾸지 않았다.
- 사용자가 이어서 요청한 EC2 3대 비용 추적은 별도 인프라/비용 점검으로 진행해야 한다.
- exact next step: `ec2-cost-and-runtime-audit`로 전환해 EC2 3대의 청구/런타임 상태를 확인하고, stockanalysis 서버 외 인스턴스 유지 여부를 판단한다.
