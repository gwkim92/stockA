# Session Handoff

## Current Status

- 완료: thesis detail API/화면에 생애주기 DTO를 추가했고, 로컬 계약/타입/빌드/AWH와 EC2 API/route smoke를 통과했다.

## Implementation Notes

- 목표: 전문 주식 분석 시스템에 필요한 thesis lifecycle을 기존 read-only 화면에 통합한다.
- API 필드: `/api/theses/{id}` payload의 `lifecycle`.
- SQL 입력: `signal.investment_thesis`, 최신 `signal.thesis_review`, 최신 `research.equity_research_artifact`.
- 화면 섹션: `투자 논리 생애주기`.
- Thesis 근거 카드의 뉴스 제목은 `ingest.source_document.korean_title`이 있으면 한국어 번역 제목을 우선 사용한다.
- 핵심 질문:
  - 왜 사는가
  - 무엇이 맞아야 하는가
  - 무엇이 틀리면 나가는가
  - 밸류에이션 민감도는 무엇인가
  - 언제 재검토하는가
- 하단 중복 카드였던 `핵심 주장`과 `무효화 조건`은 생애주기 섹션으로 통합하고, 하단은 원천 근거 추적으로만 남겼다.
- 경계:
  - 추천 weight는 바꾸지 않는다.
  - thesis write/edit 기능은 만들지 않는다.
  - 실거래 broker submit은 범위 밖이다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task thesis-lifecycle-v2`
- Passed on EC2: pulled `efb41a1`, rebuilt `apps/web`, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- Passed on EC2 service check: both services returned `active`.
- Passed on EC2 API: `/api/theses/thesis-5` returned `symbol=NVDA`, lifecycle `status=complete`, source `equity_research_artifact`, artifact `equity-research-artifact-1`, catalysts `4`, risks `3`, valuation view `true`.
- Passed on EC2 API: first thesis evidence title used Korean translation: `과열돼 보이는 4개 시장 섹터, Nvidia가 가장 큰 버블도 아니다`.
- Passed on EC2 route smoke: `/theses/thesis-5` rendered `투자 논리 생애주기`, `왜 사는가`, `무엇이 맞아야 하는가`, `밸류에이션 민감도`, and translated evidence title.

## Exact Next Step

- exact next step: 다음 작업은 `portfolio-risk-budget-policy-v2`로 섹터/테마 집중 한도와 리밸런싱 규칙을 강화하거나, `frontend-equity-research-experience-v2`로 종목/추천 상세를 전문 리서치 리포트 순서로 더 정리한다.
