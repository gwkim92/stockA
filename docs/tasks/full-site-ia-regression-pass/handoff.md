# Session Handoff

## Current Status

- 상태: completed
- completed: 전체 주요 화면의 사용자-facing 문구 회귀를 점검하고, 내부 실행 용어와 준비 중/빈값처럼 보이는 표시를 정리했다.
- 기준일: 2026-05-23

## Investigation

- 이전 패스들에서 홈, 뉴스·AI, 종목/추천/가상 거래, 운영 모니터링 화면을 각각 정리했다.
- 이번 작업은 개별 화면 개선 뒤 생길 수 있는 전체 동선 중복, 남은 내부 용어, 빈 값/에러성 표시를 한 번에 잡는 회귀 패스다.
- 대표 라우트 visible text 검사에서 `/data-health`의 `템플릿 렌더링됨`, 추천 상세의 `pipeline`/`상세 화면 준비 중`, 성과/커버리지의 `관문` 표현이 남아 있음을 확인했다.
- 공통 `AuditMetadata` 렌더러에서 `pipeline-run-*` 값을 사용자용 `실행 #...`으로 표시하고, 문자열 `"null"`은 숨기도록 정리했다.
- 추천 상세, 투자 논리 상세, 성과 측정, 포트폴리오 커버리지 문구를 사용자 판단 언어로 바꿨다.
- 카페 네트워크에서 EC2 SSH가 막혀 있었고, AWS 콘솔 계정 `115623963546`의 CloudShell로 `sg-0a2d52009e73a59e3`에 현재 IP `121.167.105.244/32` SSH 규칙을 추가했다.

## Mutable Surface

- `apps/web/src/app/**/page.tsx`
- `apps/web/src/components/*`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/full-site-ia-regression-pass/*`

## Verification

- PASS: `git diff --check`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task full-site-ia-regression-pass`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `0b9d40d`, `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active.
- PASS: EC2 `/__ready` probe succeeded.
- PASS: SSH tunnel `127.0.0.1:13000` restored after cafe IP security-group update.
- PASS: browser-rendered route text check for `/`, `/data-health`, `/intelligence`, `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/stocks`, `/stocks/QUBT`, `/recommendations`, `/recommendations/recommendation-75`, `/paper-trading`, `/trading-readiness`, `/remediation`, `/cycles`, `/performance`, `/portfolio/coverage`; all returned 200 with no blocked internal terms and no suspicious empty/error strings.

## Remaining Risks

- `dogfood-output/` is an existing untracked local artifact directory and was not changed.
- Cafe SSH allowlist is a real AWS security-group state change, not repository state. It should be reviewed later if this cafe IP should be removed.

## Exact Next Step

- exact next step: broader UX work should move from text cleanup to page-level layout prioritization, especially turning `/data-health` from log-style status into a simpler operator dashboard.
