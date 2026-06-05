# Task Contract

## Task Request

- name: `develop-branch-deployment-standard-v1`
- request: feature 단위 작업 후 개발 통합 브랜치를 최신화하고, EC2는 개발 통합 브랜치만 pull하도록 배포 시스템과 브랜치 전략을 고정한다.

## Objective

브랜치/배포 흐름을 `feature or codex task branch -> develop -> EC2 git pull develop`로 고정하고, GitHub SSH 키와 EC2 pull 방식을 문서화한다.

## Goal

- goal: `develop`이 고정 dev/integration 브랜치가 되고, EC2 `/opt/stockanalysis/app`은 task branch가 아니라 `develop`을 `git pull --ff-only origin develop`로 내려받는다.

## Mutable Surface

- mutable surface:
  - `AGENTS.md`
  - `docs/repository-publication.md`
  - `docs/tasks/develop-branch-deployment-standard-v1/*`

## Non-Goals

- GitHub Actions, deploy bot, webhook, container deploy는 이번 범위에서 만들지 않는다.
- `main` release policy는 바꾸지 않는다.
- EC2 AWS infrastructure 또는 security group은 변경하지 않는다.

## Verification

- verification command: `ssh -i /Users/woody/.ssh/id_ed25519_pusan -o IdentitiesOnly=yes -T git@github.com`
- verification command: `GIT_SSH_COMMAND='ssh -i /Users/woody/.ssh/id_ed25519_pusan -o IdentitiesOnly=yes' git ls-remote --heads origin develop`
- verification command: `git merge-base --is-ancestor develop codex/local-mvp-runtime-aws-bootstrap`
- verification command: `git push origin develop`
- verification command: `ssh ec2-user@34.206.72.213 'cd /opt/stockanalysis/app && git pull --ff-only origin develop'`
