# cycle-quality-audit-hardening-v1 Contract

## Task Request

- request: 사이클·뉴스·AI 품질 감사가 단순 중복/단일 오분류만 보는 수준에서 벗어나, 추천 입력 전에 문제를 만들 수 있는 교차 테마 불일치, 중복 흐름 근거, 약한 전파 근거까지 자동으로 드러나게 한다.
- context: 사용자는 사이클 화면과 뉴스 근거 화면에서 어떤 연결이 정상이고 어떤 연결이 오염인지 판단하기 어렵다고 지적했다.

## Goal

- goal: 기존 `cycle-ai-quality-audit-run`과 `/data-health`가 교차 테마 불일치, 중복 흐름 근거, 약한 전파 근거를 한국어로 보여주고, 추천 입력 전에 확인할 다음 조치를 제시하게 한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cycle_ai_quality_audit.py`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_cycle_ai_quality_audit.py`
  - `docs/tasks/cycle-quality-audit-hardening-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark, portfolio position, paper/live broker order flow, or order boundary.
- Do not delete data in this task. Cleanup remains a separate explicit runner.
- Do not add external paid services.
- Do not expose DB URL, bearer token, webhook URL, OAuth token, or repo-outside file paths in user-facing payloads.

## Scope

- Add cross-theme mismatch audit checks for strong news/theme incompatibility.
- Add duplicate flow evidence checks where one news title is split across multiple events and multiple cycle nodes.
- Add weak propagation evidence checks for low confidence, low impact strength, weak path weight, or missing source document linkage.
- Surface new counters and sample groups on `/data-health` in Korean.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-quality-audit-hardening-v1`

## Done Criteria

- [ ] Audit SQL emits the new counters and samples.
- [ ] Report next actions include the new audit failures.
- [ ] `/data-health` renders the new checks in Korean.
- [ ] Local verification passes.
- [ ] EC2 audit run and route smoke pass after deployment.
