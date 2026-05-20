# Recommendation Thesis Quality Evaluation View Plan

## Goal

- 추천과 투자 논리 상세 화면에서 중장기 투자 품질 판정을 read-only로 보여준다.

## Scope

- 포함:
  - 기존 recommendation/thesis DTO의 score, outcome, evidence_review, latest_review 값을 조합한다.
  - 추천 상세에 점수 강도, 근거 품질, 성과, 주문 경계를 묶은 품질 판정 패널을 추가한다.
  - 투자 논리 상세에 thesis 근거 품질, 최신 검토 조치, 무효화 조건, 주문 경계를 묶은 품질 판정 패널을 추가한다.
  - task docs와 browser verification evidence를 남긴다.
- 제외:
  - backend DTO/API 변경
  - DB migration
  - scoring formula 변경
  - recommendation/thesis 생성 로직 변경
  - live LLM/RAG call
  - scheduler host activation
  - broker/order/write flow

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/recommendations/AAPL-2024-11-01`
- browser smoke for `/theses/AAPL-bootstrap-v1`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-thesis-quality-evaluation-view`
- `git diff --check`
