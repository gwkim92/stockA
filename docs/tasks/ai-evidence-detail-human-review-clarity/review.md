# Task Review

## Result

- `/ai-evidence/[evidenceId]` 뉴스 묶음 상세의 상단 구조를 `검토 질문 + 현재 판정 + 이동 버튼`으로 변경했다.
- `ai-evidence-251`에서 검토 대상이 `SPY`로 보이던 문제를 고쳤다. 이제 검토 대상은 `금리·연준 뉴스 묶음`이고, `SPY`는 `연결 종목 후보`로 보인다.
- 사람이 확인해야 할 질문을 `같은 흐름인가`, `종목 연결이 타당한가`, `추천 입력으로 써도 되는가`, `원천부터 대조`로 분리했다.
- 상단에 `원천 뉴스부터 대조`, `SPY 종목 맥락 보기`, `연결된 추천 검토서 보기`, `뉴스 묶음으로 돌아가기` 버튼을 추가했다.
- 비용 표기를 `$0.0000` 대신 `0달러`로 바꿨다.

## Verification

- 실행한 검증:
  - `git diff --check`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-detail-human-review-clarity`
  - EC2 deploy 후 `npm --prefix apps/web run build`
  - EC2 service status: `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active
  - Playwright render check for `http://127.0.0.1:13000/ai-evidence/ai-evidence-251`

## Evidence

- EC2 deployed commit: `8c2ef87`
- Playwright screenshot: `/private/tmp/stockanalysis-runtime/ai-evidence-251-human-review-clarity.png`
- Render check result: required Korean review labels present, old misleading `대상 SPY 종목 상세 연결됨` sequence absent.

## Remaining Risks

- 검토 결과를 저장하는 완료/반려 버튼은 아직 없다. 이 기능은 write API, reviewer identity, audit log가 필요하다.
- 데이터 분류 자체의 품질 문제는 별도 task다. 이번 task는 상세 화면에서 사람이 검토 대상을 오해하지 않게 하는 범위만 처리했다.
