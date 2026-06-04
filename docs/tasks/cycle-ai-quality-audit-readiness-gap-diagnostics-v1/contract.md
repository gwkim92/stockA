# cycle-ai-quality-audit-readiness-gap-diagnostics-v1 Contract

## Task Request

- request: `cycle_ai_quality_audit`가 `degraded`일 때 숫자만 보이고 어떤 실행 단계가 부족한지 알 수 없는 문제를 해결한다.
- context: EC2 접속이 끊긴 상태에서도 다음 복구자가 정확히 어떤 runner/profile을 실행해야 하는지 판단할 수 있어야 한다.

## Goal

- goal: `cycle-ai-quality-audit-run`, `/api/data-health`, `/data-health`가 `readiness_gap_count`와 함께 누락된 실행 단계 목록을 구조화해서 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cycle_ai_quality_audit.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_cycle_ai_quality_audit.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/cycle-ai-quality-audit-readiness-gap-diagnostics-v1/*`

## Scope

- `cycle-ai-quality-audit-run` 리포트에 `readiness_gaps` 배열을 추가한다.
- `/api/data-health` visibility payload가 `readiness_gaps`를 보존하게 한다.
- `/data-health` 화면에서 누락된 실행 단계와 다음 조치를 직접 보여준다.

## Out Of Scope

- 추천 scoring weight 변경.
- broker/order submit 또는 실거래 자동화.
- 오염 데이터 삭제.
- EC2 security group, instance lifecycle, AWS 계정 설정 변경.

## Expected Behavior

- `readiness_gap_count > 0`이면 `rss_documents_missing`, `korean_translation_missing`, `ai_extraction_artifact_missing`, `hierarchical_impact_missing`, `cycle_snapshot_missing` 중 실제 누락 항목이 표시된다.
- `degraded` 설명 문구는 첫 번째 누락 단계를 사용자에게 직접 설명한다.
- 리포트는 시크릿이나 저장소 밖 파일 경로를 노출하지 않는다.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_data_health_response_includes_sanitized_cycle_ai_quality_audit`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src/stockanalysis/operations/cycle_ai_quality_audit.py`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-ai-quality-audit-readiness-gap-diagnostics-v1`

## Constraints

- EC2 `34.206.72.213`는 현재 SSH/HTTP timeout 상태이고 Chrome AWS 콘솔은 로그인되어 있지 않다. 이 작업은 로컬 코드와 문서 검증까지만 완료한다.
- EC2가 복구되면 최신 리포트를 다시 생성해 `readiness_gaps`로 정확한 누락 runner를 확인해야 한다.
