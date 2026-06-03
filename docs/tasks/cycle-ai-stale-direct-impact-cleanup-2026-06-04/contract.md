# cycle-ai-stale-direct-impact-cleanup-2026-06-04 Contract

## Task Request

- request: 최신 `cycle-ai-quality-audit-run`에서 발견된 원문 근거 없는 직접 종목 연결을 정리한다.

## Context

- `cycle-quality-audit-hardening-v1` is already implemented.
- EC2 audit refreshed on 2026-06-04 returned `cycle_ai_quality_audit_attention`.
- The latest issue sample is `event_id=19`, `symbol=NVDA`, where the source title mentions Marvell/market news but not NVIDIA/NVDA.

## Goal

- goal: 기존 cleanup runner로 원문 근거 없는 direct ticker impact를 제거하고, `cycle-ai-quality-audit-run`을 재실행해 `/api/data-health`에서 `macro_false_ticker_count=0`, `ungrounded_direct_ticker_count=0`, and `open_gates=[]` 상태를 확인한다.

## Mutable Surface

- mutable surface:
  - EC2 operational database rows affected by `cycle-ai-stale-direct-impact-cleanup-run --execute`
  - repo-outside audit artifacts under `/opt/stockanalysis/runtime/reports/`
  - `docs/tasks/cycle-ai-stale-direct-impact-cleanup-2026-06-04/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change benchmark, portfolio position, paper/live broker order flow, or order boundary.
- Do not delete source documents or events in this task.
- Do not run duplicate title cleanup in this task.
- Use the existing preview-first stale direct impact cleanup runner.

## Verification

- verification command: EC2 preview `stockanalysis-operations cycle-ai-stale-direct-impact-cleanup-run --dry-run`.
- verification command: EC2 execute `stockanalysis-operations cycle-ai-stale-direct-impact-cleanup-run --execute`.
- verification command: EC2 rerun `stockanalysis-operations cycle-ai-quality-audit-run --execute`.
- verification command: `/api/data-health` read-token smoke for refreshed audit status and open gates.
- verification command: `/data-health` route smoke.

## Done Criteria

- Preview identifies only stale direct ticker impacts.
- Execute removes stale direct ticker impacts without mutating recommendation scoring or broker/order boundary.
- Fresh quality audit reports zero direct ticker contamination.
- `/api/data-health` and `/data-health` show the cleaned audit state.
