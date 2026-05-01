# Implementation Plan

- `scripts/render_portfolio_remediation_scheduler_env_template.sh`를 추가한다.
- renderer는 repo 밖 output path만 허용하고 placeholder env template을 생성한다.
- `scripts/check_portfolio_remediation_scheduler_runtime_env.sh`를 추가한다.
- checker는 env file을 source하고 required env, placeholder, date, ticket limit, artifact root, psql command parse, wrapper preflight를 검증한다.
- `scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`를 추가한다.
- verification은 renderer/checker syntax, repo-internal path rejection, template failure, valid env success, install dry-run compatibility를 확인한다.
- `docs/portfolio-remediation-scheduler-env-readiness.md`, README, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
