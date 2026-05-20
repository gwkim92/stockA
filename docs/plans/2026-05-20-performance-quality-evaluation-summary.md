# Performance Quality Evaluation Summary Plan

## Summary
- 성과 화면에 추천/투자 논리 품질 평가 요약을 추가한다.
- 기존 추천 점수, 추천 성과, thesis review, thesis outcome을 읽기 전용으로 집계한다.
- 이번 작업은 추천 산식, DB schema, benchmark, 평가 데이터 분할을 바꾸지 않는다.

## Scope
- FastAPI/live adapter DTO에 `quality_evaluation`을 추가한다.
- Next.js 성과 화면에서 표본 수, 점수-성과 정렬, 검토-성과 불일치, 커버리지 상태를 한국어로 보여준다.
- 기존 `quality_gates`는 유지하고, 새 요약은 과대 해석 방지용 설명 레이어로 둔다.

## Non-Goals
- 추천 점수 산식 변경
- 자동 주문, paper/live order 생성
- benchmark 또는 outcome 산식 변경
- scheduler host 활성화

## Verification
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- 브라우저에서 `/performance` 확인
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task performance-quality-evaluation-summary`
- `git diff --check`
