# develop-branch-deployment-standard-v1 Handoff

## Status

- current status: completed; `develop` is the canonical dev/integration branch and EC2 now pulls from it.

## Current Status

- 완료:
  - Identified that remote has `develop`, not `dev`.
  - Confirmed `/Users/woody/.ssh/id_ed25519_pusan` authenticates to GitHub as `gwkim92`.
  - Documented `develop` as the canonical dev/integration branch.
  - Pushed latest task state to `codex/local-mvp-runtime-aws-bootstrap`.
  - Fast-forwarded and pushed `develop` to `b437f912`.
  - Switched EC2 `/opt/stockanalysis/app` checkout from `codex/local-mvp-runtime-aws-bootstrap` to `develop`.
  - Pulled `origin/develop` on EC2 with `git pull --ff-only origin develop`.
  - Restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
  - Verified EC2 internal health:
    - `stockanalysis-frontend-api.service`: `active`
    - `stockanalysis-web.service`: `active`
    - `http://127.0.0.1:8787/__health`: `status=ok`, `read_only=true`, `order_boundary=read_only_no_order`
    - `http://127.0.0.1:3000/data-health`: `200 OK`
  - Verified local tunnel route `http://127.0.0.1:13000/data-health`: `200 OK`.
- 막힌 점:
  - none currently.

## Exact Next Step

- exact next step: for future work, create a small feature/codex branch from `develop`, merge it back to `develop`, push `develop`, then have EC2 pull `origin develop`.

## Guardrails

- Do not create a separate `dev` branch while `develop` exists.
- EC2 must not remain on a task branch after deployment.
- EC2 should pull read-only HTTPS; local pushes should use the pusan SSH key.
