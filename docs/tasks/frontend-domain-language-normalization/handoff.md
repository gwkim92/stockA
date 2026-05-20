# Session Handoff

## Active Task

- 이름: frontend-domain-language-normalization
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - common label helper and selected page wording update.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: 남아 있는 감사용 ID(`performance-outcome-1`, `market-feature-*`, `pipeline-run-*`)를 사용자 화면에서는 접거나 보조 metadata로 낮추고, 클릭 가능한 원천 링크 중심으로 정리한다.

## Verification

- `cd /Users/woody/ai/stockanalysis/apps/web && npm run typecheck` passed during implementation.
- Browser smoke confirmed `/theses/AAPL-bootstrap-v1` shows Korean labels for strategy, recommendation action, theme, cycle, invalidation condition, and read-only quality copy.
- Browser smoke confirmed `/recommendations/AAPL-2024-11-01` shows Korean labels for strategy, action, score version, gate copy, and score provenance wording.
- Screenshots:
  - `/private/tmp/stockanalysis-runtime/frontend-domain-language-normalization-thesis.png`
  - `/private/tmp/stockanalysis-runtime/frontend-domain-language-normalization-recommendation.png`

## Risks

- 너무 공격적인 문장 치환은 원문 title이나 감사용 code를 훼손할 수 있다. 따라서 known token replacement만 적용하고 감사용 code는 필요한 경우 괄호 안에 유지한다.
- 이 작업은 UI wording normalization이며 backend payload, score/action rule, DB, trading, scheduler를 바꾸지 않았다.
