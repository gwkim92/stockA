# Session Handoff

## Active Task

- 이름: frontend-audit-metadata-disclosure
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - audit metadata disclosure component and page wiring.
  - recommendation detail score provenance cards now show meaningful links/labels first and hide raw IDs in metadata.
  - thesis detail evidence cards now show performance/event links first and hide raw IDs in metadata.
  - metadata disclosure was browser-verified by opening "추적 ID 보기".
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: 남아 있는 `recommendation_bucket_avoid`, `score_below_0.3500` 같은 rule code를 user-facing chip과 audit code로 분리한다. 현재는 설명 문장 안 괄호로 남겨 auditability를 유지했다.

## Verification

- `cd /Users/woody/ai/stockanalysis/apps/web && npm run typecheck && npm run build` passed.
- Browser smoke `/theses/AAPL-bootstrap-v1`: default evidence cards show "성과 근거 보기", "이벤트 원장 열기", and collapsed "추적 ID 보기" instead of visible raw IDs.
- Browser smoke `/recommendations/AAPL-2024-11-01`: score cards show "AI 근거 열기" or "연결 화면 없음" and collapsed "추적 ID 보기" instead of visible `market-feature-*`/`pipeline-run-*` IDs.
- Browser metadata click confirmed "추적 ID 보기" expands and exposes raw IDs for audit.
- Screenshots:
  - `/private/tmp/stockanalysis-runtime/frontend-audit-metadata-disclosure-thesis.png`
  - `/private/tmp/stockanalysis-runtime/frontend-audit-metadata-disclosure-recommendation.png`

## Risks

- 감사 가능성을 잃지 않기 위해 raw ID는 제거하지 않는다. 기본 화면에서만 감춘다.
- 일부 가격 feature 점수는 아직 별도 상세 화면이 없으므로 "연결 화면 없음"으로 표시한다. 원천 추적은 metadata에서 가능하다.
