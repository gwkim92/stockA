# develop-branch-deployment-standard-v1 Handoff

## Status

- current status: in progress; policy docs updated locally, develop merge/push and EC2 pull pending.

## Current Status

- 완료:
  - Identified that remote has `develop`, not `dev`.
  - Confirmed `/Users/woody/.ssh/id_ed25519_pusan` authenticates to GitHub as `gwkim92`.
  - Documented `develop` as the canonical dev/integration branch.
- 진행 중:
  - Merge latest task branch into `develop`.
  - Push `develop`.
  - Switch EC2 checkout to `develop` and pull from it.
- 막힌 점:
  - none currently.

## Exact Next Step

- exact next step: commit the branch/deployment policy docs on the task branch, fast-forward `develop`, push it, and update EC2 to pull `develop`.

## Guardrails

- Do not create a separate `dev` branch while `develop` exists.
- EC2 must not remain on a task branch after deployment.
- EC2 should pull read-only HTTPS; local pushes should use the pusan SSH key.
