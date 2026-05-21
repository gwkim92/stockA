# Session Handoff

## Active Task

- 이름: frontend-news-ai-evidence-ux
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - `AiEvidenceDetailData`에 `news_candidate`와 `retrieval_context_summary`를 추가했다.
  - live adapter가 `news_event_candidate` artifact를 detail response에서 그대로 `evidence_type=news_event_candidate`로 반환하게 했다.
  - event list DTO에 `ai_evidence_type`, `ai_evidence_provider`, `ai_evidence_confidence`를 추가했다.
  - `/ai-evidence/[evidenceId]`에 뉴스 AI 후보 전용 섹션을 추가했다.
  - `/events`와 `/intelligence`에서 뉴스 AI 후보/묶음 증거 라벨과 provider/confidence를 보여주도록 바꿨다.
  - 데이터 수집/분석 지도 문구를 “로컬 규칙만 분석”이 아니라 “규칙 분류 + Codex OAuth 후보 분석” 흐름으로 정정했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: EC2에 최신 코드를 배포하고 `/events`, `/intelligence`, `/ai-evidence/<news_event_candidate>` 화면 smoke를 확인한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: pass, 45 tests.
- `bash scripts/verify_frontend_api_contract.sh`: pass.
- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-news-ai-evidence-ux`: pass.
- EC2 DB direct SQL smoke for event list: pass, returned `ai_evidence_type=news_event_candidate`, provider `codex_oauth`, confidence value.
- EC2 DB direct SQL smoke for `ai-evidence-10`: pass, returned `news_event_candidate`, provider `codex_oauth`, candidate impacts and retrieval context.

## Risks

- 이 작업은 read-only UX 개선이며 추천 산식, 스케줄러, 거래 실행은 바꾸지 않는다.
- EC2 service deploy and web smoke are still pending in this session.
