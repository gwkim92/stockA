# Frontend Rule Rationale Disclosure Plan

## Goal

- thesis review 근거 문장 안의 rule code를 기본 화면에서 분리한다.
- 사용자는 "추천 버킷이 회피 대상", "추천 점수가 기준 미만" 같은 설명을 먼저 보고, `recommendation_bucket_avoid`, `score_below_0.3500` 같은 code는 접힌 metadata에서 확인한다.

## Scope

- 포함:
  - thesis detail latest review rationale rendering
  - rule signal chip UI
  - audit metadata disclosure for raw rule codes and original change notes
  - task docs
- 제외:
  - backend DTO shape changes
  - DB/schema changes
  - thesis review action rule changes
  - scoring changes
  - AI/RAG generation
  - trading/scheduler behavior

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/theses/AAPL-bootstrap-v1`
- browser click smoke for "검토 rule code 보기"
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-rule-rationale-disclosure`
- `git diff --check`

## Implementation Note

- `latest_review.change_notes`는 화면에서 바로 노출하지 않고 signal chip과 접힌 audit metadata로 분리한다.
- 사용자 기본 화면은 한국어 설명을 우선한다.
- 감사/디버깅에 필요한 원문과 rule code는 "검토 rule code 보기" disclosure에 남긴다.
