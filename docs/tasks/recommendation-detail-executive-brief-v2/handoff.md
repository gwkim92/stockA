# recommendation-detail-executive-brief-v2 Handoff

## Current Status

- completed: implementation, local verification, EC2 deployment, and browser QA are complete.
- 완료: 구현, 로컬 검증, EC2 배포, 브라우저 QA까지 완료.
- 시작 커밋: `ec224330`.
- 브랜치: `codex/recommendation-detail-executive-brief-v2`.
- develop commits:
  - `bf654886` Add recommendation executive brief
  - `0669eeb3` Polish recommendation brief copy
  - `b2c187b1` Fix recommendation brief Korean wording

## Context

- Previous task `recommendation-detail-position-ux-v1` added read-only `position_context` and a `포지션 현실` section.
- `recommendation-471` is `SPY`; EC2 data shows it is not held in `Long Term Paper`, so no average cost exists.
- The remaining UX issue is that the recommendation detail page is still too long and decision-critical facts are scattered.

## Next Step

- exact next step: continue reducing lower recommendation detail sections, especially long evidence/audit blocks, into progressive disclosure that follows `판단 요약 -> 보유/포지션 -> 가치/근거 -> 위험/거래 경계`.

## Verification Evidence

- `cd apps/web && npm test -- --run`
- `cd apps/web && npm run typecheck && npm run build`
- `bash scripts/verify_frontend_api_contract.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-executive-brief-v2`
- EC2 `develop` pull, `apps/web` production build, and `stockanalysis-web` restart completed.
- EC2 browser QA at `http://127.0.0.1:13000/recommendations/recommendation-471` passed at `375px`, `768px`, and `1280px`: no failed responses, no horizontal overflow, executive brief visible, `미보유`, `추천 비중 4%`, `목표가 자료가 아직 부족`, `6/7개 충족`, `실거래 차단` visible, and no `pipeline`, `runner`, `artifact`, `cost_basis`, `valuation snapshot`, `자료이` terms inside the brief.

## Notes

- `recommendation-471` is `SPY`; current EC2 data has no SPY holding row in `Long Term Paper`, so average cost cannot be shown. The page now distinguishes this as `미보유` rather than leaving the user to infer a missing value.
- No recommendation scoring weight, benchmark, portfolio position, broker submit, order boundary, or DB schema was changed.
