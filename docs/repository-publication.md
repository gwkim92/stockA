# Repository Publication

이 문서는 public GitHub repository `git@github.com:gwkim92/stockA.git`에 올릴 코드와 제외할 대상을 정의한다.

## Repository

- remote: `git@github.com:gwkim92/stockA.git`
- visibility: public
- SSH key used locally: `/Users/woody/.ssh/id_ed25519_pusan`
- public key fingerprint: `SHA256:eoQlrg9nUtVYZ3/8w+SIsrwqktOrS0/YIgrRZp4a1Qk`

## Branch Strategy

- `main`: public stable branch. Only verified code and docs are pushed here.
- `develop`: integration branch for continuing implementation after initial publication.
- `feature/<task-slug>`: task branches for reviewable changes.
- `release/<date-or-version>`: future release stabilization branch if deployment starts.
- hotfix branches: `hotfix/<issue-slug>` only for urgent corrections to `main`.

Rules:

- `main` must pass the relevant verification script before push.
- `develop` may contain integration work, but should still pass task-level verification before merging to `main`.
- risky changes such as schema, benchmark, evaluation, auth, secrets, broker integration, or deployment require task contract and explicit verification evidence.
- public push must not include private keys, real API keys, local runtime env files, generated dependency directories, build outputs, or scheduler activation files.

## Publishable

- application source under `src/` and `apps/web/src/`.
- docs under `docs/`.
- task contracts, plans, handoffs, and reviews.
- database migrations and seed SQL that contain no real credentials.
- test fixtures that are synthetic or public-source sample data.
- `.env.example` with placeholder values only.
- verification scripts.
- package manifests and lockfiles.

## Not Publishable

- `.env` or `.env.*` except `.env.example`.
- private SSH keys or key material.
- real API keys, tokens, passwords, cookies, or session files.
- local runtime scheduler env files.
- generated dependency directories such as `node_modules/`.
- build outputs such as `.next/`.
- Python caches such as `__pycache__/`.
- local logs, temporary artifacts, or machine-specific launchd/cron activation files.

## First Publication Decision

Initial publication should push the verified current state to `main`, then create `develop` from the same commit. Future implementation continues on task branches from `develop`.
