# Ingest Bootstrap

## Goal

이 문서는 실제 시장/거시/공시 데이터를 가져오는 `수집기 계층`의 첫 구조를 고정한다.

현재 범위는 다음 3가지다.

- 초기 데이터 소스 선택
- 소스별 요청 빌더와 CLI 골격
- 후속 DB 적재 단계와의 경계 정의

## Why Separate Collectors Matter

seed는 기준정보를 넣는 용도다.

- 시장 코드
- 거래소
- 데이터 소스 목록

반면 실제 투자 판단에 쓰는 데이터는 모두 수집기가 가져와야 한다.

- 가격/거래량
- 재무/실적
- 거시지표
- 공시
- 뉴스/정책 문서

즉 seed와 collector는 역할이 다르다.

## Initial Source Selection

### 1. SEC EDGAR

역할:

- filings 메타데이터
- company submissions history
- companyfacts 기반 재무 facts

선정 이유:

- `data.sec.gov`의 submissions, companyfacts API는 공식 SEC 소스다.
- 공식 문서는 인증/API key 없이 접근 가능하다고 설명한다.
- 공식 문서는 실시간 업데이트와 fair access 가이드라인(사용자당 초당 10요청 이하)을 명시한다.

공식 문서:

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC Developer Resources](https://www.sec.gov/about/developer-resources)

### 2. FRED

역할:

- 금리
- 인플레이션
- 실업률
- PMI 대체 거시 시계열
- 장단기 금리차, 유동성 등 매크로 signal 입력

선정 이유:

- 미국 거시지표 bootstrap에는 가장 표준적인 공식 소스 중 하나다.
- FRED API v1/v2와 series/observations 계열이 공식 문서로 명확하다.
- API key가 필요하므로 로컬 환경변수 기반으로 붙인다.

공식 문서:

- [FRED API](https://fred.stlouisfed.org/docs/api/fred/)
- [FRED API Keys](https://fred.stlouisfed.org/docs/api/api_key.html)

### 3. Alpha Vantage

역할:

- 미국 주식 일봉 adjusted OHLCV bootstrap
- 일부 fundamentals bootstrap

선정 이유:

- 공식 문서가 일봉 adjusted price, 재무제표, earnings 계열을 제공한다.
- 공식 지원 페이지는 free key와 현재 free usage 제한을 명시한다.

중요:

- 이 선택은 `bootstrap source` 기준이다.
- 더 큰 유니버스, 더 높은 호출량, 더 강한 품질 요구가 생기면 이후 교체될 수 있다.
- 이 평가는 공식 문서에 나온 현재 제공 범위를 바탕으로 한 초기 구현용 판단이다.

공식 문서:

- [Alpha Vantage Documentation](https://www.alphavantage.co/documentation/)
- [Alpha Vantage Support](https://www.alphavantage.co/support/)

## Bootstrap Architecture

현재 ingest 계층은 아래 구조로 시작한다.

1. source adapter
2. request builder
3. CLI execution entrypoint
4. 이후 raw payload 저장/정규화/DB 적재 단계로 연결

현재 구현 범위:

- `src/stockanalysis/ingest/sources/`
- `src/stockanalysis/ingest/registry.py`
- `src/stockanalysis/ingest/cli.py`

아직 하지 않은 것:

- DB insert/upsert
- scheduling
- retry persistence
- raw artifact storage write
- backfill state management

## Environment Variables

초기 collector는 아래 환경변수를 사용한다.

- `STOCKANALYSIS_SEC_USER_AGENT`
- `STOCKANALYSIS_FRED_API_KEY`
- `STOCKANALYSIS_ALPHA_VANTAGE_API_KEY`

SEC는 key가 아니라 식별 가능한 `User-Agent`가 필요하다.
FRED와 Alpha Vantage는 API key가 필요하다.

## CLI Scope

현재 CLI는 아래를 지원한다.

- source 목록 출력
- source/dataset 설명
- request dry-run 생성
- 실제 fetch 실행

예시:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli list-sources
PYTHONPATH=src python3 -m stockanalysis.ingest.cli describe-source sec
PYTHONPATH=src python3 -m stockanalysis.ingest.cli build-request fred series_observations --param series_id=CPIAUCSL
PYTHONPATH=src python3 -m stockanalysis.ingest.cli build-request sec submissions --param cik=0000320193
```

## Verification Scope

현재 검증은 아래까지다.

- request builder unit test
- CLI basic smoke
- Python compile check

실제 외부 fetch를 기본 검증에 넣지 않은 이유:

- API key/usage limit/환경변수 의존성이 있다.
- bootstrap 단계에서는 deterministic local verification을 우선한다.

## Recommended Next Step

이후 구현은 아래 순서가 자연스럽다.

1. `macro-ingest`
2. `sec-filings-ingest`
3. `market-data-ingest`
4. `universe-bootstrap`

또는 시장 데이터를 먼저 보고 싶으면 `market-data-ingest`를 앞당겨도 된다.
