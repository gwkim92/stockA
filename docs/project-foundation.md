# Project Foundation

## Project Definition

이 프로젝트는 거시경제, 정치, 기술, 산업, 기업 흐름을 지속적으로 해석하고, 수많은 섹터/테마의 개별 사이클을 추적하며, 중기·중장기·장기 투자 관점에서 유망 종목을 선별하고, 추천 이후에도 그 판단이 유효한지 계속 검토하는 AI 기반 투자 운영 시스템을 만드는 것이다.

핵심은 `추천` 자체보다 `판단의 생성, 기록, 검토, 개선`이다.

## What We Are Actually Building

우리가 만들려는 것은 단순한 주식 추천 앱이 아니다.

아래를 동시에 수행하는 시스템이다.

1. 시장을 계속 읽는다.
2. 섹터와 테마를 각각 독립적인 사이클로 추적한다.
3. 그 흐름이 어떤 종목에 연결되는지 해석한다.
4. 중장기 투자 thesis를 만든다.
5. 추천 이후에도 thesis가 살아 있는지 계속 재검토한다.
6. 시간이 지나면서 추천 성과와 실패 원인을 누적 분석한다.

즉 이 프로젝트는 `AI 종목 추천기`보다 `사이클 기반 투자 판단 운영 체계`에 가깝다.

## Core Requirements

### 1. Continuous Market Understanding

시스템은 시장을 정적으로 보지 않는다.

- 거시경제 변화
- 정책 변화
- 지정학 이벤트
- 기술 트렌드 변화
- 산업 업황 변화
- 기업 실적 변화

이 모든 정보를 지속적으로 수집하고 현재 해석 상태를 업데이트해야 한다.

### 2. Theme And Sector Cycle Tracking

모든 섹터와 테마는 같은 속도로 움직이지 않는다.

예를 들어 AI, 반도체, 전력설비, 원전, 방산, 바이오, 2차전지, 금융, 소비재는 각각 다른 리듬과 촉매를 가진다.

따라서 시스템은 단순히 "좋은 종목"을 고르는 것이 아니라 다음을 추적해야 한다.

- 어떤 테마가 초기 형성 구간인지
- 어떤 섹터가 확산 구간인지
- 무엇이 과열인지
- 무엇이 조정 중인지
- 어디서 재상승 가능성이 생기는지
- 어떤 산업은 구조적으로 종료 국면인지

### 3. Long-Horizon Investment Focus

이 프로젝트는 초단타나 하루짜리 시그널 시스템이 아니다.

목표는 아래 기간의 판단을 지원하는 것이다.

- 중기: 3개월 내외
- 중장기: 3~12개월
- 장기: 1년 이상

따라서 추천 구조도 단기 매매보다 `투자 논리`, `보유 근거`, `무효화 조건` 중심이어야 한다.

### 4. Ongoing Position Review

추천이 한 번 나갔다고 끝나면 안 된다.

시스템은 추천 또는 보유 종목에 대해 계속 질문해야 한다.

- 추천 당시 논리가 아직 유효한가
- 정책, 거시, 실적 변화가 thesis를 강화했는가 약화했는가
- 지금도 신규 매수 가능한가
- 줄여야 하는가
- 교체해야 하는가
- 단순 조정인가, 사이클 종료인가

### 5. Performance And Decision Audit

잘 투자하고 있는지 알려면 수익률만 보면 안 된다.

반드시 아래를 기록해야 한다.

- 추천 시점의 근거
- 당시 점수와 상태
- 이후 성과
- 성과의 원인
- 잘된 판단과 잘못된 판단의 차이

이 프로젝트는 시간이 지날수록 자기 판단을 평가하고 개선할 수 있어야 한다.

## Product Principles

- LLM은 최종 투자 의사결정자가 아니라 `해석기`와 `리포터` 역할을 맡는다.
- 실제 추천은 재현 가능한 점수, 규칙, 상태 판정 로직을 기반으로 해야 한다.
- 모든 추천은 당시 데이터, 점수, 근거, 무효화 조건을 함께 저장해야 한다.
- 추천보다 `검토 가능성`이 더 중요하다.
- 자동화는 평가 기준이 고정된 뒤에만 붙인다.

## System Architecture

### 1. Market Data Layer

정형 데이터 수집과 저장을 담당한다.

- 주가, 거래량, 시가총액
- 섹터/산업 분류
- 재무제표, 밸류에이션
- 이익 추정치
- 금리, CPI, 실업률, PMI 등 거시지표
- 환율, 채권, 원자재
- ETF 흐름, 기관/외국인 수급

### 2. Event Intelligence Layer

비정형 문서를 이벤트로 구조화한다.

- 뉴스
- 공시
- 실적 발표
- 정책 발표
- 정치 이벤트
- 산업 보고서
- 기술 트렌드 자료

주요 출력 예시:

- event_type
- related_themes
- related_sectors
- related_symbols
- direction
- confidence
- time_horizon

### 3. Theme/Sector Knowledge Graph

테마, 섹터, 산업, 기업의 연결을 저장한다.

- 테마 정의
- 테마별 종목 매핑
- 선행/후행 관계
- 공급망 연결
- 거시 민감도
- 정책 수혜/규제 민감도

### 4. Cycle Engine

테마/섹터/산업의 현재 국면을 판정한다.

판정 근거:

- 가격 추세
- 상대강도
- 거래대금
- 수급
- 실적 추정 변화
- 뉴스/정책 이벤트 밀도
- 업황 지표
- 밸류에이션 부담

대표 상태:

- 초기 형성
- 상승 확산
- 실적 확인
- 과열
- 조정
- 바닥 형성
- 재상승 준비
- 구조적 종료

### 5. Stock Thesis Engine

종목 단위 투자 논리를 만든다.

각 thesis는 최소한 아래를 가진다.

- symbol
- linked_theme
- linked_sector
- thesis_summary
- supporting_factors
- risks
- invalidation_conditions
- expected_holding_period
- benchmark
- review_schedule

### 6. Recommendation Engine

종목을 단순 추천이 아니라 버킷별로 분류한다.

- 장기 코어
- 중장기 사이클 수혜
- 관찰 후보

점수 구성 예시:

- macro_fit_score
- cycle_score
- industry_score
- fundamental_score
- earnings_revision_score
- valuation_score
- event_score
- risk_penalty

### 7. Portfolio Review Engine

현재 보유 또는 추천 종목의 상태를 지속 검토한다.

- 유지
- 비중 확대
- 비중 축소
- 신규 매수 가능
- 관찰 유지
- thesis 약화 경고
- 퇴출 후보

### 8. Performance Attribution Layer

성과를 원인별로 나눠 본다.

- 종목 선택 효과
- 섹터 배분 효과
- 테마 노출 효과
- 거시 민감도 효과
- 이벤트 대응 효과
- 손실 원인 분류

### 9. AI Decision Console

사람이 시스템에 질문하고 결과를 읽는 인터페이스다.

예시 질문:

- 지금 강해지는 테마는 무엇인가
- 최근 3개월간 사이클이 개선된 섹터는 무엇인가
- 장기 코어 후보 상위 10개는 무엇인가
- 보유 종목 중 thesis가 약화된 것은 무엇인가
- 포트폴리오가 어떤 거시 시나리오에 취약한가

## Initial Product Scope

처음부터 전세계 멀티에셋으로 가지 않는다.

초기 범위는 아래처럼 제한한다.

- 시장: 미국 또는 한국 중 1개 시장부터 시작
- 유니버스: 100~300개 대표 종목
- 시간축: 일봉 중심
- 투자 기간: 중기·중장기·장기
- 출력: 추천, 관찰, 제외, 경고, 검토 리포트
- 거래: 실거래 자동 집행 없이 페이퍼트레이딩 우선

## Recommended Delivery Sequence

### Phase 0. Foundation

- 프로젝트 목적과 범위 고정
- 데이터/평가 원칙 고정
- 추천 대상 시장과 유니버스 확정

### Phase 1. Data Backbone

- 가격/재무/거시/뉴스 적재 파이프라인 구축
- 기본 시계열 저장 구조 확정

### Phase 2. Theme And Cycle Modeling

- 테마/섹터/산업 그래프 설계
- 사이클 판정 규칙 1차 버전 구축

### Phase 3. Thesis And Recommendation

- 종목 thesis 저장 구조 설계
- 중장기 추천 규칙 엔진 구축

### Phase 4. Review And Attribution

- 추천 이후 검토 루프 구축
- 성과 추적과 원인 분석 추가

### Phase 5. Operator Interface

- 대시보드 또는 콘솔
- AI 리포트와 질의 인터페이스

## What Success Looks Like

성공한 시스템은 아래를 할 수 있어야 한다.

- 현재 시장에서 강해지는 테마와 약해지는 테마를 설명한다.
- 단순 종목 추천이 아니라 왜 그 종목이 중장기적으로 유효한지 설명한다.
- 추천 이후에도 thesis가 깨졌는지 강화됐는지 자동 검토한다.
- 수익과 손실을 단순 결과가 아니라 판단 품질 관점에서 해석한다.

## What We Should Not Do Early

- 처음부터 실시간 초단타 시스템으로 확장
- 백테스트 없이 LLM에게 바로 종목 추천을 맡김
- 모든 국가와 모든 종목을 한 번에 커버
- 자동매매부터 붙임
- 평가 기준이 없는 상태에서 자동화 루프를 돌림
