# Task Contract

## Task

- 이름: ai-autonomous-review-boundary
- 요청: 뉴스 근거, 추천, 보유 논리의 검토를 사람 검토가 아니라 AI 자동 검토로 전환한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: read-only 투자 판단 화면과 API 품질 상태는 `사람 검토 가능/필요`가 아니라 `AI 검토 통과/필요/보류`로 표현한다. AI와 validator가 통과한 근거는 추천·보유 검토 입력으로 자동 승격될 수 있고, 차단/주의 항목은 보강 대상으로 남는다.

## Why

- 이 서비스의 목적은 사람이 뉴스를 수동으로 읽고 승인하는 것이 아니라, AI가 뉴스·공시·가격·테마 흐름을 구조화하고 검증해 장기 투자 운영 입력을 만드는 것이다.
- 사람이 매번 검토해야 하는 표현은 자동 운영 시스템의 목표와 맞지 않는다.

## Scope

- 포함:
  - frontend API read model의 accepted evidence/recommendation/thesis quality status를 AI review 용어로 전환
  - 화면 문구와 한국어 label helper의 `사람 검토` 표현 정리
  - 기존 `ready_for_human_review`, `human_review_required` 값이 남아 있어도 한국어 화면에서는 AI 검토 표현으로 표시
  - task 문서와 검증 기록 갱신
- 제외:
  - DB schema rename
  - 실제 broker/live order 자동 승인
  - kill switch, order limit, broker boundary 해제
  - 새로운 유료 AI/RAG/온톨로지 서비스 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `src/stockanalysis/ingest/news/translation.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/signal/thesis.py`
  - `src/stockanalysis/signal/portfolio_holding_thesis.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_portfolio_holding_thesis_bootstrap.py`
  - `docs/tasks/ai-autonomous-review-boundary/*`
- 수정 금지 파일:
  - `.env`/secret 값
  - trading DB schema와 broker submit code
  - live broker credential/permission 설정

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task ai-autonomous-review-boundary`

## Done Criteria

- 추천/투자 논리 품질 상태의 통과값이 `ai_review_passed`로 내려온다.
- 이벤트/AI 근거의 accepted quality gate가 `ai_review_passed` 또는 AI review pending 계열로 내려온다.
- 화면에서 일반 사용자에게 보이는 `사람 검토` 표현이 AI 자동 검토 표현으로 바뀐다.
- 뉴스 번역/클러스터/보유 thesis 산출물에 신규 `사람 검토/사람 승인` 문장이 생성되지 않는다.
- 실거래 주문 안전 경계는 해제하지 않는다.
