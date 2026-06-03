# cycle-recommendation-paper-wording-clarity-v1 Handoff

## Current Status

- in progress: local implementation and local verification are underway.

## Decisions

- This is a wording and screen-clarity task only.
- Do not imply a missing manual review button on recommendation or paper trading pages.
- Use `근거`, `상태`, `후보`, `감사 기록`, and `읽기 전용` wording where the system is only displaying evidence or blocking actions.
- Preserve broker/order boundary: all trading remains read-only and no broker submit path is enabled.

## Changes

- `/cycle-map` now labels AI-derived flow as `AI 근거 흐름` and points users to the news/AI evidence screen rather than an ambiguous AI judgment screen.
- `/recommendations` now labels passed evidence as `AI 검증 통과`, ready recommendation boundaries as `판단 근거 충족`, and recommendation detail links as `추천 상세`.
- `/paper-trading` now describes paper trading as simulation and audit-boundary evidence, replacing action-less review wording with candidate confirmation and audit-record wording.

## Verification

- passed: text scan found no `AI 검토`, `상세 검토 가능`, `검토 입력 부족`, `추천 검토서`, `후보 검토`, `읽기 전용 검토`, `검토 기록`, `AI 판단`, or `추천 검토` in the three target pages.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`

## Next Step

- exact next step: run AWH verify, commit/push, deploy to EC2, and smoke `/cycle-map`, `/recommendations`, and `/paper-trading`.
