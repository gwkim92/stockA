# Task Contract

## Task

- 이름: operating-cockpit-information-architecture
- 요청: 화면이 무엇을 보여주려는지 이해하기 어렵고 중복되는 내용이 많으므로, 깊게 고민해 정보 구조를 운영 판단 순서 중심으로 다시 정리한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 사용자가 홈과 분석 지도에서 `수집 상태 -> 뉴스/AI 해석 -> 종목 영향 -> 추천/보유 검토 -> 거래 안전` 순서로 무엇을 먼저 봐야 하는지 이해하고, 상세 원장 화면은 필요한 순간에만 열 수 있다.

## Findings

- 상단 메뉴가 구현 산출물 기준으로 많아져서 사용자의 daily workflow가 보이지 않는다.
- 홈 화면의 추상 그래프와 설명은 프로젝트 방향은 말하지만 오늘 무엇을 확인해야 하는지 답하지 못한다.
- `/intelligence`는 뉴스 묶음, 개별 AI 후보, 전체 이벤트 trace를 한 화면에 길게 반복해 핵심과 원장을 구분하기 어렵다.
- 기존 영어 `news_event_candidate` artifact가 성공 상태로 남아 있으면 새 한국어 prompt version 재실행 후보에서 제외될 수 있다.
- AI 근거 상세 화면은 모델 실행 정보와 원천 청크가 먼저 보여서, 사용자가 "이 뉴스가 어떤 종목/추천/보유 검토에 영향을 주는가"를 먼저 알기 어렵다.

## Scope

- 포함:
  - 상단 내비게이션을 핵심 daily workflow로 축소
  - 홈 화면을 오늘의 점검 순서와 보완 큐 중심으로 재구성
  - 분석 지도에서 대표 이벤트만 보여주고 상세 원장은 `/events`, `/ai-evidence`로 분리
  - 분석 지도의 저장 뉴스 묶음과 임시 로컬 묶음 중복을 하나의 판단 보드로 통합
  - AI 근거 상세를 종목/추천/보유 연결 중심으로 재배치
  - `news_event_candidate` 후보 선택을 prompt template version 기준으로 재실행 가능하게 보강
  - focused test, Next type/build, AWH verify, EC2 smoke
- 제외:
  - DB schema 변경
  - 추천 점수 산식 변경
  - broker/order flow 변경
  - 유료 외부 RAG/온톨로지 서비스 도입

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `tests/test_news_rss_ai_extract.py`
  - `docs/tasks/operating-cockpit-information-architecture/`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring/evaluation baseline
  - broker/order submission code
  - scheduler deployment manifests

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task operating-cockpit-information-architecture`
  - Browser smoke for `/`, `/intelligence`, `/ai-evidence`, `/events`

## Done Criteria

- [ ] 홈에서 오늘의 점검 순서가 명확하다.
- [ ] 헤더가 핵심 화면만 노출하고 상세 원장은 페이지 내부 링크로 접근된다.
- [ ] 분석 지도에서 뉴스 묶음과 개별 AI 후보의 역할이 구분된다.
- [ ] AI 근거 상세에서 종목/추천/보유 연결 여부가 모델 실행 기록보다 먼저 보인다.
- [ ] 과거 영어 AI artifact가 새 한국어 prompt version 재실행을 막지 않는다.
- [ ] 검증 명령과 EC2 smoke를 통과한다.
