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
  - EC2에 최신 코드를 배포하고 FastAPI/Next systemd service를 재시작했다.
  - 터널 화면에서 `/ai-evidence/ai-evidence-10`와 `/events`의 핵심 한국어 marker가 렌더링되는 것을 확인했다.
- 막힌 점:
  - 없음.

## Exact Next Step

- exact next step: recommendation scoring/review 화면에서 이 뉴스 AI 후보 evidence가 어떤 추천/보유검토 판단에 사용됐는지 추적하는 연결을 강화한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: pass, 45 tests.
- `bash scripts/verify_frontend_api_contract.sh`: pass.
- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-news-ai-evidence-ux`: pass.
- EC2 DB direct SQL smoke for event list: pass, returned `ai_evidence_type=news_event_candidate`, provider `codex_oauth`, confidence value.
- EC2 DB direct SQL smoke for `ai-evidence-10`: pass, returned `news_event_candidate`, provider `codex_oauth`, candidate impacts and retrieval context.
- EC2 deploy: `git pull --ff-only`, `/opt/stockanalysis/venv/bin/python -m pip install -e .`, `npm --prefix apps/web run build`, `systemctl restart stockanalysis-frontend-api.service stockanalysis-web.service`: pass, both services active.
- EC2 API smoke: authorized `GET /api/ai-evidence/ai-evidence-10` returned `news_event_candidate`, provider `codex_oauth`, 1 theme impact, 1 instrument impact, 5 known themes.
- Tunnel web smoke: `http://127.0.0.1:13000/ai-evidence/ai-evidence-10` contained `뉴스 AI 후보 근거`, `RAG-lite`, `테마와 종목 영향 후보`, `Codex`, `이벤트 원장 열기`; `/events` contained `뉴스 AI 후보`, `codex`, `신뢰도`.

## Risks

- 이 작업은 read-only UX 개선이며 추천 산식, 스케줄러, 거래 실행은 바꾸지 않는다.
