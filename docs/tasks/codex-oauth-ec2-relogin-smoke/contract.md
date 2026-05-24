# Task Contract

## Task

- 이름: codex-oauth-ec2-relogin-smoke
- 요청: EC2에서 Codex OAuth를 재로그인한 뒤 실제 LLM batch 분석이 다시 성공하는지 검증한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: EC2 `/opt/stockanalysis/app`가 최신 브랜치 코드를 실행하고, `stockanalysis-operations cycle-community-ai-summary-v2-run --provider codex_oauth --execute`가 fallback이 아니라 실제 `codex_oauth` 성공 invocation을 남긴다.

## Scope

- 포함:
  - EC2 SSH 접근 확인
  - 최신 git revision 배포
  - FastAPI/Next.js restart 및 상태 확인
  - EC2 Codex CLI 로그인 상태 확인
  - 실제 Codex OAuth batch smoke 실행
  - DB/API/data-health에서 성공 invocation 확인
- 제외:
  - Codex OAuth token 파일 직접 읽기/복사
  - OpenAI API key로 우회
  - FastAPI request 중 실시간 LLM 호출
  - 추천 score weight 변경
  - live broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `docs/tasks/codex-oauth-ec2-relogin-smoke/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
- 수정 금지 파일:
  - Codex OAuth token/auth files
  - `.env` secret values
  - 추천 scoring weight
  - broker/order submit path
  - DB schema

## Required Preconditions

- EC2 SSH 보안그룹이 현재 작업 위치의 공인 IP를 허용해야 한다.
- AWS 콘솔 또는 CLI에서 대상 EC2 인스턴스를 관리할 수 있어야 한다.
- EC2의 `ec2-user`에서 Codex CLI 재로그인이 완료되어야 한다.

## Smoke Commands

```bash
ssh -i /Users/woody/Downloads/settle.pem ec2-user@98.86.164.57 'echo ok && hostname && date'
```

```bash
cd /opt/stockanalysis/app
git pull --ff-only origin codex/local-mvp-runtime-aws-bootstrap
/opt/stockanalysis/venv/bin/python -m compileall -q src tests
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
sudo systemctl restart stockanalysis-frontend-api.service stockanalysis-web.service
systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service
```

```bash
cd /opt/stockanalysis/app
PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m stockanalysis.operations.cli \
  cycle-community-ai-summary-v2-run \
  --env-file /opt/stockanalysis/runtime/data-operations.env \
  --as-of-date 2026-05-24 \
  --node-code TECH_DOMAIN \
  --limit 1 \
  --max-nodes 1 \
  --provider codex_oauth \
  --reasoning-effort low \
  --execute
```

## Verification

- 검증에 사용할 명령:
  - `ssh -i /Users/woody/Downloads/settle.pem -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new ec2-user@98.86.164.57 'echo ok && hostname && date'`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task codex-oauth-ec2-relogin-smoke`
- EC2 접근 복구 후 검증에 사용할 증거:
  - `ai.model_invocation.provider='codex_oauth' and status='succeeded'`
  - `ai.cycle_community_summary.summary_type='cycle_community_ai_v2'`
  - `/api/data-health`에서 Codex OAuth 성공 run 확인
  - `http://127.0.0.1:13000/cycle-map`가 LLM summary를 fallback 없이 표시

## Done Criteria

- 최신 브랜치 commit이 EC2에 반영되어 있다.
- 실제 Codex OAuth provider invocation이 성공했다.
- fallback-only 결과를 성공으로 간주하지 않는다.
- 실패 시 실패 원인이 `token_invalidated`, AWS 접근, SSH 보안그룹, Codex CLI 미설치 중 무엇인지 구분해 handoff에 남긴다.
