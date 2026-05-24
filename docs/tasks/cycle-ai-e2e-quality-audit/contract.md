# Task Contract

## Task

- 이름: cycle-ai-e2e-quality-audit
- 요청: RSS 수집, 한국어 번역, Codex OAuth 분석, validator, hierarchical propagation, cycle snapshot, recommendation component, paper validation 상태를 한 번에 감사하는 backend CLI와 화면 가시성을 추가한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations cycle-ai-quality-audit-run --as-of-date YYYY-MM-DD --execute`가 DB에서 오염/준비도 지표를 계산하고, repo-outside JSON artifact와 `/data-health` 품질 감사 카드로 노출할 수 있다.

## Scope

- 포함:
  - 새 operations module과 CLI command
  - 중복 뉴스, quantum→energy 오분류, 원문 근거 없는 direct ticker, macro-only false ticker 감사
  - 번역/AI artifact/전파/cycle/recommendation/paper validation count 감사
  - `ops.pipeline_run` 실행 이력 기록
  - `/api/data-health`와 `/data-health` 화면 노출
  - unit/API/frontend contract tests
- 제외:
  - 오염 데이터 삭제
  - AI prompt/schema 변경
  - recommendation score weight 변경
  - scheduler profile 자동 편입
  - live broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/cycle_ai_quality_audit.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/`
  - `docs/tasks/cycle-ai-e2e-quality-audit/*`
- 수정 금지 파일:
  - `.env` secret values
  - recommendation scoring formula weights
  - DB migration/schema
  - scheduler activation/systemd unit files

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_data_operations_cli tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-ai-e2e-quality-audit`

## Done Criteria

- 새 CLI가 dry-run/execute/output/repo-outside boundary를 지원한다.
- execute mode가 `ops.pipeline_run`에 성공/실패 이력을 남긴다.
- `/api/data-health` DTO에 `cycle_ai_quality_audit`이 포함된다.
- `/data-health`에서 품질 감사 상태, 오염 의심, 번역 커버리지, paper validation 상태를 한국어로 볼 수 있다.
- 테스트와 하네스 검증이 통과한다.
