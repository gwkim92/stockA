# operations-console-boundary-cleanup-v1 Contract

## Request

- `/data-health`를 투자 화면이 아닌 운영 콘솔로 정리한다.

## Scope

- Top cards: 수집, 분석, AI, 스케줄러, provider quota, 배포 상태.
- Detailed runner/pipeline/artifact data moves below fold or into details.
- Investor pages only link to operations when data trust is affected.

## Invariants

- No scheduler cadence change.
- No backend/runtime config change.

## Verification

- `/data-health` remains useful for operators.
- Investor pages do not inherit operations language.
- E2E operations route scan passes.
