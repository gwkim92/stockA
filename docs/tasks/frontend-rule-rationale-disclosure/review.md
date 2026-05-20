# Task Review

## Summary

- Thesis detail의 "최근 검토 이유" 영역에서 rule code를 기본 화면과 분리했다.
- 기본 화면은 `추천 버킷이 회피 대상`, `추천 조치가 제외`, `추천 점수가 최소 기준 0.3500 미만` 같은 사람이 읽는 signal chip을 보여준다.
- 감사 추적용 원문 `change_notes`, action code, rule code는 "검토 rule code 보기" 접힘 영역에 보존했다.
- Backend DTO, DB schema, scoring, thesis review action rule, trading, scheduler behavior는 변경하지 않았다.

## Verification Evidence

- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- Browser smoke `/theses/AAPL-bootstrap-v1`: default view hides raw rule codes and shows Korean reason chips.
- Browser click smoke "검토 rule code 보기": expanded metadata shows raw `recommendation_bucket_avoid`, `recommendation_action_exclude`, `score_below_0.3500`.
- Screenshot: `/private/tmp/stockanalysis-runtime/frontend-rule-rationale-disclosure-thesis.png`.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-rule-rationale-disclosure`: passed.
- `git diff --check`: passed.

## Residual Risks

- Parser is intentionally conservative. If future backend `change_notes` format changes substantially, the UI falls back to displaying the translated original note rather than dropping information.
- This is a UI disclosure improvement only. It does not improve recommendation quality or add AI analysis, trading, or scheduler activation.
