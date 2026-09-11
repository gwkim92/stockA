# 기존 기업 보고서의 주요 주장 대조

대상은 2026-09-10 기준 보고서 492(NVDA), 493(AAPL), 494(ARM), 실제 생성 모델 gpt-5.6-terra/codex_oauth다. 이번 검토는 2026-09-11에 수행한 AI 보조 원문 대조다. 당시 입력의 진실성과 오늘 확인한 공식 원문을 구분하며, 9/10 이후 발표를 과거 주장의 근거로 쓰지 않는다. 아래는 주요 주장 표본이며 전체 문장에 대한 사실 인증은 아니다.

## NVDA — artifact 492

| 주장 | 판정 | 대조와 조치 |
|---|---|---|
| 직접 재무 지표가 unavailable이며 SEC에 필요한 사실이 없다 | 불일치 | 입력의 unavailable 표시는 재현되지만 원인은 선택 오류다. 주식 수만 있는 2026-02-20 대신 2026-01-25가 실제 연간 결산이다. 매출 215,938백만달러, 순이익 120,067백만달러가 DB와 [공식 FY2026 실적](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Fourth-Quarter-and-Fiscal-2026/default.aspx)에 있다. |
| 상대지표·relative_multiple 가격 범위 | 내부 기록 일치, 경제적 타당성 미검증 | 230.345 기준가, 241.777166 기준 범위 등은 선택 입력과 일치한다. AI Labor and Productivity는 직접 경쟁사 집합으로 검증되지 않았다. 내재가치 검증이나 독립 시장 사실이 아니다. |
| 9/7 Strong Results 기사만 있어 실적 수치가 없다 | 입력 범위 확인, 수집 부족 | 보고서 입력은 제목 수준이다. 하지만 8/26 [FY2027 Q2 공식 실적](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/default.aspx)과 [10-Q](https://investor.nvidia.com/files/doc_financials/2027/NVDA-2027-Q2-10Q-Final-including-exhibits.pdf)가 존재한다. 7/26 종료 매출 96,221백만달러를 SEC API에서도 확인했다. |
| 20bn Groq 기사와 랙 출시는 촉매로 확정할 수 없다 | 미확인 유지 | 선택 RSS만으로 거래 유형·금액 의미·회계 영향은 입증되지 않는다. 제목 금액을 계약 매출이나 인수가격으로 확정하지 않는다. |
| 현재 thesis는 당시 불변 기록이 아니다 | 입력 메타데이터와 일치 | current_record_not_versioned를 보존한다. 현재 내용의 존재를 과거 시점 지식으로 승격하지 않는다. |

## AAPL — artifact 493

| 주장 | 판정 | 대조와 조치 |
|---|---|---|
| 2025-10-17 연간 순이익·capex·OCF가 없어 재무를 확인할 수 없다 | 불일치 | 주식 수 날짜를 잘못 선택했다. 9/27 종료 FY2025 매출 416,161백만달러, 순이익 112,010백만달러, OCF 111,482백만달러, capex 12,715백만달러가 DB에 있다. 매출/순이익은 [공식 FY2025 발표](https://www.apple.com/newsroom/2025/10/apple-reports-fourth-quarter-results/), 현금흐름은 이번 SEC companyfacts 표본과 대조했다. |
| Macro Rates and Fed 피어 적합성 미검증 | 확인 | 실제 비교군과 일치한다. 거시 테마의 연결만으로 동종 사업 비교군을 확정하지 않는다는 설명이 맞다. |
| 제품 가격 인상, 비용 부담, 마진 영향 | 부분 확인 | 9/9 [공식 iPhone Duo 발표](https://www.apple.com/newsroom/2026/09/apple-unveils-iphone-duo/)는 시작 가격 1,999달러와 제품 발표를 확인한다. 시장 예상 대비 인상 폭, 회사 비용 흡수, 판매량·마진 효과는 입증하지 않는다. |
| 통신사 프로모션·MacBook 2종 계획 철회 | 미확인 | 연결 RSS는 확인되나 대상·조건·실제 수요/실적 영향의 공식 근거를 이번 표본에서 확보하지 못했다. 확정 촉매로 처리하지 않는다. |
| 입력 문서 4개가 근거 | 보완 필요 | 그중 source-document-22는 이전 기사 식별자 충돌로 격리됐다. 주요 주장·촉매의 직접 인용은 확인되지 않았지만 과거 입력 이력이 남아 있다. 해당 보고서 전체를 검토 통과로 올리지 않는다. |
| 최신 회사 실적 정보의 충분성 | 부족 | 7/30 [FY2026 Q3 공식 실적](https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/)이 있다. 6/27 종료 매출은 분기, OCF는 9개월 누적이므로 같은 분기비율로 나누면 안 된다. 원천 시작일을 보존해야 한다. |

## ARM — artifact 494

| 주장 | 판정 | 대조와 조치 |
|---|---|---|
| FY2025 gross/operating/net margin 약 96.98%/20.74%/19.77% | 확인, 해당 기간 한정 | [FY2026 20-F의 비교 재무](https://investors.arm.com/node/8281/html)에서 2025 매출 4,007, gross profit 3,886, operating income 831, net income 792백만달러를 확인했다. 비율이 일치한다. |
| FY2025 OCF margin 9.9077%, FCF margin 4.4422% | 확인, 계산 정의 한정 | 같은 공시의 OCF 397, capex 219백만달러로 397/4007, (397-219)/4007이 일치한다. 2026년 현재 수익성으로 확대하지 않는다. |
| 매출 비교연도가 없어 성장률 검증 불가능 | 불일치 | 2024 매출 3,233백만달러는 공시와 DB에 있다. 서로 다른 결산연도가 같은 fiscal_year=2025로 저장되어 이전 연도를 찾지 못한다. 공개 자료 부재로 설명하면 안 된다. |
| 자체 데이터센터 칩은 제목 수준이고 제품 출시·고객 정보 없음 | 입력 범위 확인, 공식 근거 누락 | [3/24 Arm AGI CPU 공식 발표](https://newsroom.arm.com/news/arm-agi-cpu-launch)는 제품과 Meta 협업을 명시한다. 이는 회사 발표 사실의 근거이며 매출·수익성 실현의 독립 검증은 아니다. |
| Red Hat 협력 | 부분 확인 | [공식 협력 설명](https://newsroom.arm.com/blog/agentic-ai-infrastructure-arm-agi-cpu-red-hat)이 있다. 계약 규모·실현 매출은 입증하지 않는다. |
| 2025 지표로 장기 사업을 판단 | 최신성 부족 | 5/26 FY2026 20-F와 7/29 FY2027 Q1 자료가 공개됐다. [실적 목록](https://investors.arm.com/financials/quarterly-annual-results)과 SEC companyfacts의 6-K를 확인했지만 운영 입력은 2025 연간이다. |
| below_peer는 사업 열위 근거 | 미검증 | 실제 저장 백분위는 존재하지만 AI Labor and Productivity는 사업 경쟁사 검증을 거치지 않았다. 직접적인 경쟁력 결론으로 사용하지 않는다. |

## 화면 기록의 적용 범위

`research_review_records.py`는 세 보고서의 정확한 fingerprint에만 위 보완 판정을 적용한다. 보고서 ID·기준일·모델·요약·각 본문 목록·민감도·입력 문서·생성시각 중 하나가 바뀌면 이 기록을 적용하지 않는다. 신규 보고서, 같은 ID의 fixture, 다른 내용은 `not_recorded`다. 원 보고서는 보존하고 새 AI 호출은 수행하지 않았다.
