# Session Handoff

## Current Status

- 상태: completed
- current status: completed
- 완료: AI 추출 필드, 투자 논리 요약, 검토 기준 문구에 남은 raw code 표현을 사용자용 한국어 문구로 정리했다.
- 기준일: 2026-05-23

## Investigation

- `/ai-evidence/ai-evidence-136`의 추출 필드에 `QUANTUM_COMPUTING_POLICY / supportive / ...`, `chunk-news-ai-*` 값이 그대로 보인다.
- `/stocks/QUBT`와 `/ai-evidence/ai-evidence-136`의 투자 논리 카드에 `QUBT watch 투자 논리 via US Market Breadth`가 남아 있다.
- 이 문제는 DB 오염이라기보다 표시 계층에서 raw structured value를 그대로 보여준 결과다.

## Implemented

- `/ai-evidence/[evidenceId]`의 AI 추출 필드 값 렌더러를 분리해 `테마/종목 · 방향. 근거` 형태로 표시한다.
- `chunk-news-ai-*` 근거 ID를 `뉴스 후보 근거`, `테마 영향 근거`, `종목 영향 근거`로 바꿨다.
- `korean-labels`의 embedded replacement를 보강해 `QUANTUM_COMPUTING_POLICY`, `US Market Breadth`, `supportive`, `watch thesis via ...`가 긴 문장 안에서도 사용자용 한국어로 보이게 했다.
- `/theses/[thesisId]`의 `검토 rule code 보기` 문구를 `검토 세부 기준 보기`로 바꾸고, hidden metadata label도 사람용 표현으로 정리했다.
- EC2 배포 커밋: `5cb6b35`.

## Verification Log

- 로컬: `cd apps/web && npm run typecheck`
- 로컬: `cd apps/web && npm run build`
- 로컬: `git diff --check`
- 로컬: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task detail-code-value-wording-cleanup`
- EC2: `git pull --ff-only`, `npm --prefix apps/web run typecheck`, `npm --prefix apps/web run build`, `sudo systemctl restart stockanalysis-web.service`
- EC2: `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service` -> both `active`
- EC2 route smoke: `/ai-evidence/ai-evidence-136`, `/stocks/QUBT`, `/theses/thesis-13` -> HTTP 200, Server Components error marker 없음
- EC2 text smoke: AI 상세에서 `테마 영향 근거`, `종목 영향 근거`, `양자컴퓨팅·정책 수혜 · 우호적` 확인
- EC2 text smoke: 투자 논리 상세에서 `핵심 테마는 미국 시장 참여도이고`, `검토 세부 기준 보기` 확인
- Playwright snapshot: `/ai-evidence/ai-evidence-136?refresh=5cb6b35`, `/stocks/QUBT?refresh=84cac61`, `/theses/thesis-13?refresh=5cb6b35`

## Remaining

- 일부 원천 뉴스 제목과 기사 요약은 원문 보존 목적상 영어로 남는다.
- React key나 hidden audit 원문에는 원본 문자열이 남을 수 있지만, 일반 사용자 화면의 주요 판단 문구는 한국어 label 경로를 거친다.
- 전체 사이트의 모든 hidden metadata를 한국어화하는 작업은 별도 UI copy audit task로 계속 진행해야 한다.

## Mutable Surface

- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/detail-code-value-wording-cleanup/*`

## Exact Next Step

- exact next step: 다음 UI copy audit slice에서 `/intelligence`, `/recommendations/[id]`, `/paper-trading`의 운영자용/개발자용 문구를 더 걷어낸다.
