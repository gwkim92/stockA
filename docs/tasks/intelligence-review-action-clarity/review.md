# Task Review

## Result

- `/intelligence` 상단에 “검토 시작” 패널을 추가했다.
- 검토 순서를 `뉴스 묶음`, `개별 뉴스 후보`, `추천 연결`, `차단 후보`로 고정했다.
- 뉴스 묶음 카드에 묶인 기준, 종목 관계, 추천 영향, 원문 대조 체크리스트를 추가했다.
- 개별 뉴스 후보 카드에 원문/종목/추천 연결을 어떤 순서로 확인해야 하는지 표시했다.
- 현재 서비스가 read-only라서 “검토 완료/반려” 저장 버튼은 없고, 버튼은 근거 화면으로 이동한다는 경계를 노출했다.

## Verification

- 실행한 검증:
  - `git diff --check`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task intelligence-review-action-clarity`
  - EC2 deploy 후 `npm --prefix apps/web run build`
  - EC2 service status: `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active
  - Playwright render check for `http://127.0.0.1:13000/intelligence`

## Evidence

- 최종 EC2 commit: `e9c42d9`
- Playwright screenshot: `/private/tmp/stockanalysis-runtime/intelligence-review-action-clarity-final.png`
- Render check result: required Korean review labels present, forbidden production error text absent.

## Remaining Risks

- 실제 완료/반려 저장은 아직 없다. 이 기능은 write API, approver identity, audit log 설계가 필요하다.
- 데이터 분류 품질은 별도 문제다. 이번 task는 페이지 검토 행동을 명확히 하는 범위만 처리했다.
