# recommendation-thesis-detail-decision-ux-v1 handoff

## Status

- current status: in progress.
- completed: local code edits, Next typecheck, and Next build.
- pending: AWH verification, commit/push, EC2 deploy, and EC2 route smoke.

## Changes

- Recommendation detail now separates paper validation input from broker order status in the first decision panel.
- Recommendation detail copy replaces internal `thesis`, `artifact`, `gate`, and `weight` wording where it appeared in user-facing Korean text.
- Thesis detail copy replaces mixed English/Korean gate and artifact wording with Korean decision wording.
- Recommendation waterfall metric grid now supports four decision metrics without awkward wrapping.

## Verification

- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Pending: AWH verify
- Pending: EC2 deploy and route smoke

## Exact Next Step

- exact next step: run AWH verification, then deploy to EC2 and smoke `/recommendations/<id>` and `/theses/<id>`.

## Notes

- 화면 가시성 개선만 수행한다.
- 추천 weight, broker/order boundary, portfolio state, benchmark는 변경하지 않는다.
