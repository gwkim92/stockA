# Task Contract

## Task

- 이름: operating-cockpit-trust-repair
- 요청: 실패/오염 데이터 정리, 운영 화면 문구와 정보 구조 정비, 뉴스 AI 근거/종목 연결/가상 거래 상태를 사람이 이해할 수 있게 개선한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - EC2 DB에서 실패한 Codex OAuth 호출과 참조 없는 실패 run 이력이 정리된다.
  - `/data-health`는 수집·뉴스 AI·캔들·추천·가상 거래 자동 실행 상태를 관제 화면처럼 보여준다.
  - `/intelligence`와 `/ai-evidence/...`는 뉴스가 왜 묶였고 어떤 종목/테마와 어떤 관계인지 설명한다.
  - `/stocks/...`는 직접 뉴스, 상위 흐름 전파, 추천/보유/가격 연결을 분리해서 보여준다.
  - `/paper-trading`과 `/trading-readiness`는 지금이 테스트/차단/승인 후보 중 어디인지 명확히 보여준다.

## Scope

- 포함:
  - 실패 `ai.model_invocation` 및 참조 없는 실패 `ops.pipeline_run` 정리
  - 뉴스 묶음 근거 설명 강화
  - 종목 연결 사유와 전파 경로 표시
  - 페이퍼 거래 상태와 차단/승인 후보 설명 강화
  - 반복되는 운영 설명 문구 제거 또는 축소
  - task handoff와 검증 기록 갱신
- 제외:
  - 실거래 broker order submit 구현
  - 추천 점수 산식 대규모 변경
  - 유료 뉴스/RAG/온톨로지 외부 서비스 도입
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/operating-cockpit-trust-repair/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler cadence
  - broker/order submit code

## Verification Commands

- 검증에 사용할 명령:
  - EC2 DB cleanup dry-run/count verification
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-cockpit-trust-repair`

## Done Criteria

- [ ] Failed runtime data is deleted without deleting valid AI artifacts.
- [ ] UI wording no longer repeats system-internal explanations as primary content.
- [ ] News cluster cards show grouping basis, representative evidence, and stock/theme relation.
- [ ] Paper trading and trading readiness expose current test status clearly.
- [ ] Local verification passes.
- [ ] EC2 deployment and smoke verification pass.
