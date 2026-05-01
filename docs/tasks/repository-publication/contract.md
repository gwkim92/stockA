# Task Contract

## Task

- 이름: repository-publication
- 요청: local SSH key `pusan`을 사용해 public GitHub repo `git@github.com:gwkim92/stockA.git`에 현재 프로젝트 코드를 안전하게 등록한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: public repo에 safe initial snapshot이 push되고, branch strategy와 공개/비공개 파일 기준이 문서화된다.

## Why

- 프로젝트가 로컬에만 존재하면 이력 추적, 백업, 협업, 브랜치 기반 작업 진행이 어렵다.
- public repo이므로 secret과 generated artifacts를 올리지 않는 기준이 필요하다.

## Scope

- 포함:
  - `pusan` SSH key 확인
  - remote repository 상태 확인
  - `.gitignore` 공개 안전 기준 보강
  - repository publication 문서 작성
  - Git 초기화, branch strategy 적용
  - safe initial commit
  - `main`과 `develop` push
- 제외:
  - GitHub branch protection UI 설정
  - secret scanning service 설정
  - CI workflow 추가
  - 실제 API key/credential 추가

## Mutable Surface

- 수정 가능한 파일:
  - `.gitignore`
  - `README.md`
  - `docs/repository-publication.md`
  - `docs/tasks/repository-publication/`
- 수정 금지 파일:
  - private SSH key files
  - real runtime env files
  - deployment secrets
  - generated dependency/build directories
- 검증에 사용할 명령:
  - `ssh-keygen -lf /Users/woody/.ssh/id_ed25519_pusan.pub`
  - `git ls-remote git@github.com:gwkim92/stockA.git`
  - `find . -path './apps/web/node_modules' -prune -o -path '*/__pycache__' -prune -o -name '*.env' -o -name '.env' -o -name '*.pem' -o -name '*.key' -o -name 'id_*' -print`
  - `rg -n "(BEGIN .*PRIVATE KEY|OPENAI_API_KEY\s*=|ANTHROPIC_API_KEY\s*=|GITHUB_TOKEN\s*=|ghp_[A-Za-z0-9_]+|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})" . -S --glob '!apps/web/node_modules/**' --glob '!**/__pycache__/**' --glob '!apps/web/.next/**' --glob '!docs/tasks/repository-publication/plan.md'`
  - `bash scripts/verify_apps_web_scaffold.sh`
  - `git status --short --ignored`
  - `git push origin main`
  - `git push origin develop`

## Completion Criteria

- [ ] `pusan` public key fingerprint이 확인된다.
- [ ] secret/generated artifact scan이 수행된다.
- [ ] `.gitignore`가 public repo 기준으로 보강된다.
- [ ] branch strategy 문서가 존재한다.
- [ ] Git repo가 초기화되고 remote가 설정된다.
- [ ] safe initial commit이 생성된다.
- [ ] `main` branch가 remote에 push된다.
- [ ] `develop` branch가 remote에 push된다.
- [ ] handoff/review가 갱신된다.

## Risks

- public repo에 secret을 올리면 회수해도 노출 이력이 남는다.
- remote가 빈 저장소가 아니면 강제 push 없이 병합 전략을 다시 판단해야 한다.
- GitHub branch protection은 로컬에서 완전히 보장할 수 없다.
