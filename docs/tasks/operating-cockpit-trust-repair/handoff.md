# Session Handoff

## Current Status

- 상태: deployed_and_smoked
- 기준일: 2026-05-22
- 완료:
  - 사용자 불만 지점을 데이터 오염, 모니터링 화면, 뉴스 AI 근거, 종목 연결, 페이퍼 거래 가시성으로 분리했다.
  - EC2에서 `codex_oauth` 실패 호출 201건을 확인했다.
  - 실패 호출은 artifact를 만들지 않았고, 정상 artifact 52건과 rejected artifact 5건은 성공 호출에 연결된 검증 결과임을 확인했다.
  - 삭제 후보 run은 23개로 확인했다: 실패/오염 `event_intelligence_llm_extract` run 22개와 실패 `news_rss_upsert` run 1개.
  - 삭제 후보 run은 `ops.pipeline_run` 외부 참조가 없음을 확인했다.
  - EC2 DB에서 실패 `ai.model_invocation` 201건과 참조 없는 실패 `ops.pipeline_run` 23건을 transaction으로 삭제했다.
  - 삭제 후 EC2 DB 확인 결과: 실패 Codex invocation 0건, 실패 pipeline run 0건, fallback pipeline run 0건, 성공 Codex invocation 57건, accepted candidate 52건, rejected candidate 5건.
  - `/api/ai/news-clusters?limit=1` summary에서 `llm_candidate_success_count=57`, `llm_candidate_failed_count=0`, `llm_candidate_artifact_count=52`, latest provider `codex_oauth`를 확인했다.
  - 뉴스 묶음 API payload에 `relation_reasons`를 추가해 묶음 기준, 직접 종목, 원천 문서, RAG 청크 상태를 내려준다.
  - `/`, `/data-health`, `/intelligence`, `/ai-evidence/[evidenceId]`, `/stocks/[symbol]`, `/paper-trading`, `/trading-readiness`의 반복 내부 문구와 모호한 wording을 정리했다.
  - `/intelligence`와 AI 근거 상세에서 “왜 묶였나” 근거를 직접 노출한다.
  - `/paper-trading`은 가상 승인 후보와 broker 제출 건수를 함께 보여주고, 후보가 없을 때 empty state를 보여준다.

## Cleanup Plan

- 삭제 완료 대상:
  - `ai.model_invocation` where `provider='codex_oauth' and status='failed'`
  - `ops.pipeline_run` 중 실패 호출만 가진 Codex run 및 status `failed`/`succeeded_with_fallback`이면서 외부 참조가 없는 run
- 보존 대상:
  - 성공 `news_event_candidate`
  - 성공 호출에서 만들어진 `news_event_candidate_rejected`
  - `news_cluster_summary`
  - `event.event`, `event.event_classification_impact`, `event.event_instrument_impact`, `signal.propagated_instrument_impact`

## Verification Log

- PASS: EC2 cleanup execute and post-count.
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-cockpit-trust-repair`
- PASS: Git commit/push `5fe7cd4`.
- PASS: EC2 pull to `5fe7cd4`.
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`.
- PASS: EC2 `cd apps/web && npm run typecheck && npm run build`.
- PASS: EC2 service restart: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active.
- PASS: EC2 API smoke confirmed `/api/ai/news-clusters?limit=1` has `llm_candidate_failed_count=0`, latest provider `codex_oauth`, and `relation_reasons`.
- PASS: EC2 page smoke 200: `/`, `/data-health`, `/intelligence`, `/paper-trading`, `/trading-readiness`, `/stocks/SPY`, `/ai-evidence/ai-evidence-122`, `/recommendations/recommendation-52`.
- PASS: local tunnel smoke: `http://127.0.0.1:13000/intelligence` returned 200 and contains “왜 이 뉴스들이 같이 묶였나”.

## Exact Next Step

- exact next step: use the live site at `http://127.0.0.1:13000` and continue page-by-page UX review; next code pass should focus on remaining English source titles and improving raw ticker/theme labels without changing data contracts.
