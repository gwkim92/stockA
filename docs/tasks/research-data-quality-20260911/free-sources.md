# 무료 데이터 원천과 적용 순서

공식 문서와 페이지를 2026-09-11에 확인했다. 무료 원천의 추가 구독료와 개발·저장·운영 비용은 다르다. 무료 열람이 원문 전체 재배포 권리를 뜻하지도 않는다. 이번 작업은 조사 및 공개 GET 표본 검증이며 새 계정·키·유료 서비스·운영 스케줄은 추가하지 않았다.

## 1순위: SEC와 기업 공식 자료

**SEC Submissions / Companyfacts / 원문 공시**는 현재 재무 부족을 가장 직접적으로 해결한다. [공식 API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)는 키 없이 JSON을 제공한다. 공시 중 submissions는 통상 1초 이내, XBRL API는 통상 1분 이내 갱신되며 bulk ZIP은 야간 갱신된다. [접근 정책](https://www.sec.gov/about/webmaster-frequently-asked-questions)은 초당 최대 10요청이다. 초기 구현은 식별 가능한 기존 User-Agent, 캐시, 재시도 간격과 초당 2요청 이하부터 시작하는 것이 적절하다.

- 이번에 NVDA/AAPL/ARM companyfacts 모두 HTTP 성공과 실제 재무 개념을 확인했다. 새 API 키가 필요하지 않았다.
- companyfacts는 표준 taxonomy와 기업 전체 범위 수치를 제공한다. 회사 고유 세그먼트·지역·제품·계약·가이던스는 10-K/10-Q/20-F/6-K 및 실적 첨부 원문을 함께 읽어야 한다.
- 수집 기준을 단일 CIK/제한된 확장에서 활성 기업별 공시 변화 감지와 순환 갱신으로 확장한다. 원문 accession·filed·period·unit·concept을 보존한 뒤 정규화한다.
- 단순 “API 성공” 대신 세 기업의 최근 연간·분기 원문 대조를 첫 완료 기준으로 둔다.

**기업 IR/공식 Newsroom**은 뉴스 제목을 기업의 직접 발표와 연결하는 무료 경로다. [NVIDIA 실적](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/default.aspx), [Apple 실적](https://www.apple.com/newsroom/2026/07/apple-reports-third-quarter-results/), [ARM 공시·실적](https://investors.arm.com/financials/quarterly-annual-results)을 우선 대상으로 삼는다. 세 사이트에 필요한 최근 발표가 실제 존재한다.

실적 HTML/PDF와 발표일·원문 URL·내용 hash·인용 구간을 연결하고 SEC 수치와 교차 대조한다. 기업이 발표한 제품/고객/가이던스와 실제 매출·계약 이행을 분리한다. 외부 기사 유료벽을 우회하지 않는다.

## 2순위: 거시 공식 통계와 발표 당시 이력

| 원천 | 보완할 항목 | 무료 접근과 한계 | 적용 방법 |
|---|---|---|---|
| [FRED/ALFRED](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) | 현재 16시계열의 장기 이력, 고용·PCE·GDP, 수정 이력 | [계정 API 키 필요](https://fred.stlouisfed.org/docs/api/api_key.html). 기본 조회는 오늘 알고 있는 수정된 이력이다. | 기존 FRED 연결을 이용하되 realtime_start/end와 [vintage dates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html)를 보존한다. 현재 값과 당시 알려진 값을 섞지 않는다. |
| [BLS Public Data API](https://www.bls.gov/developers/api_faqs.htm) | CPI·고용·임금의 공식 원천 대조 | 무료 등록 v2: 하루 500요청, 요청당 50시계열·20년. 등록은 매년 갱신. 무등록은 더 작은 한도. | FRED 수치와 발표 캘린더를 교차 확인한다. API 한도는 전체 수정 이력 제공 보장이 아니다. |
| [BEA Open Data](https://www.bea.gov/open-data) | GDP·소비·소득·산업별 부가가치 | API 키 등록이 필요하며 데이터별 발표 주기가 다르다. | PCE/GDP를 먼저 추가하고 [공식 API 안내](https://apps.bea.gov/api/_pdf/bea_web_service_api_user_guide.pdf)의 단위·기간 메타데이터를 저장한다. |
| [EIA Open Data](https://www.eia.gov/opendata/documentation.php) | 원유 재고·생산·소비·에너지 수급 | API는 무료 키, bulk는 키 없이 가능하다. | 에너지 가격만으로 사이클을 판단하지 않도록 수급 발표를 보완한다. 새 [키 등록](https://www.eia.gov/opendata/register.php)은 아직 수행하지 않았다. |

현재 실행 목록에서 빠진 UNRATE/PCEPI/GDPC1과 10~20년 이력부터 추가하는 것이 우선이다. 발표시각·수정일·수집시각을 나눠 저장하며, 기존 백테스트의 데이터 분할이나 평가 기준은 별도 변경 없이 유지한다.

기존 FRED 키로 UNRATE의 2024년 1~2월 관측값을 realtime=2024-03-08 및 2026-09-10으로 두 번 조회해 모두 HTTP 200을 확인했다. 이번 두 표본은 각각 3.7/3.9로 같았으므로 수정이 발생한 사례를 검증한 것은 아니다. 시점 지정 조회가 가능하다는 증거이며, DB 적재나 발표시각 복구는 아직 수행하지 않았다. `probe_alfred.py`, 로컬 `alfred-probe.json`에 기록했다.

정치·규제 사건은 [Federal Register API](https://www.federalregister.gov/reader-aids/developer-resources/rest-api)와 [BIS 공식 발표](https://www.bis.gov/news-updates/search?content_type=All)로 보완할 수 있다. Federal Register는 키 없이 CSV/JSON을 제공하며 1994년 이후 문서 검색이 가능하다. 한 검색의 페이지 이동은 2,000건까지이므로 날짜로 나눠 수집한다. 제안 규칙·최종 규칙·발표일·시행일을 구분하고 공식 govinfo PDF까지 연결한다. 반도체 수출통제 발표가 있다는 사실과 개별 기업 매출에 미친 영향은 별도 검증한다. 이번에는 공식 접근 문서를 확인했으며 API의 운영 수집기는 설치하지 않았다.

## 3순위: ETF 공식 보유·비용·NAV

[SSGA SPY](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy), [Invesco QQQ](https://www.invesco.com/qqq-etf/en/about.html), [iShares IVV](https://www.ishares.com/us/products/239726/ishares-core-sp-500-etf)는 공식 상품 정보와 보유내역 다운로드 경로가 있다. SSGA/Invesco는 이미 프로젝트에 수집기가 있으므로 신규 기능인 것처럼 다시 만들지 않고 갱신 상태·일별 보존·가중치 합·상위 편입 종목을 확인한다. QQQ 페이지의 보유 목록은 조사 도구에서 동적 로딩 실패가 있었으므로 페이지 접근만으로 해당 날짜 파일 수집 성공을 주장하지 않는다.

현재 보유내역을 과거 구성 종목으로 소급 적용하지 않는다. 변경 중인 목록은 관측일별로 보존해야 이후 집중도·벤치마크 편향을 비교할 수 있다.

## 가격 데이터: 무료 후보와 현실적인 제약

- **기존 Twelve Data**: [Basic 가격표](https://twelvedata.com/pricing)는 무료 8 API credits/min, 800/day를 제시한다. 개인용 internal/non-display 조건을 함께 확인해야 한다. [가격 조정 문서](https://support.twelvedata.com/en/articles/5179064-are-the-prices-adjusted)의 일·주·월봉 split 조정과 배당 총수익을 혼동하지 않는다. 현재 계정 약관·화면 제공 권한 전체를 이번 조사로 인증한 것은 아니다.
- **Alpaca**: [공식 FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)에 무료 실시간 IEX와 SIP의 차이, 15분 이상 지난 historical SIP 조회 조건이 설명돼 있다. IEX는 단일 거래소 범위다. 독립 가격 교차 확인의 후보지만 실제 계정 권한·조정 방식·이력 범위를 먼저 표본 검증해야 한다. 새 계정이나 거래 연결을 만들지 않았다.
- **Alpha Vantage**: [공식 한도](https://www.alphavantage.co/premium/)의 무료 25요청/일은 작은 표본 비교에는 가능하나 72종목의 빈번한 운영 수집을 대체하기에는 작다. 모든 endpoint가 무료라고 전제하지 않는다.

회사 가이던스는 공식 실적·공시에서 무료로 보완할 수 있다. 그러나 기관별 예상치·수정 이력·과거 컨센서스를 완전하게 제공하는 무료 대체재는 이번 조사에서 확인하지 못했다. 가이던스를 컨센서스로 이름만 바꾸지 않는다.

## 실행 순서와 확인 기준

1. **재무 파서와 원문 연결**: AAPL/NVDA/ARM 기간·단위·수치 대조, 6-K와 capex 개념 검토. 그다음 활성 대상 순환 갱신. 수집 성공과 계산 검증을 각각 기록한다.
2. **공식 본문 수집**: 세 기업의 최근 실적·공식 발표를 원문으로 보존하고 보고서 주요 주장에 구간 단위 연결. RSS 제목만 있는 주장은 미확인으로 유지한다.
3. **거시 빈티지·장기 이력**: 고용/PCE/GDP부터, 발표 주기에 맞는 최신성 판정과 수정 전후 구분. 과거 시점 재현 검사를 추가한다.
4. **가격·기업행동·ETF 이력**: 직전 거래일 커버리지와 조정 의미 검증, 무료 대체 원천의 표본 대조 후 도입 여부 판단.
5. 위 근거가 마련된 뒤 필요한 보고서만 재생성한다. 원천 품질 개선과 모델 등급 변경은 별도 판단이다. 이번 작업에서 AI를 다시 호출하거나 자동 추천 weight를 변경하지 않았다.
