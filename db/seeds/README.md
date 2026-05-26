# Database Seeds

이 디렉터리는 migration 이후 바로 넣을 수 있는 최소 bootstrap 데이터를 둔다.

현재 범위:

- 시장 기준정보
- 거래소 기준정보
- 초기 데이터 소스 목록
- 거시/테마/섹터 ontology-lite seed
- 주요 미국 주식/ETF의 초기 sector/theme exposure seed
- 포트폴리오 drift smoke용 명시적 수동 benchmark composition seed

목적:

- ingest 파이프라인 시작점 제공
- 개발/검증 환경에서 lookup 데이터 보장
- 운영 범위와 데이터 소스 선택을 문서화된 seed로 고정

현재 seed는 `미국 시장 MVP` 기준이다.
향후 한국 시장이나 추가 공급자를 붙일 때 별도 seed 파일을 추가한다.

`0005_sector_classification_seed.sql`는 포트폴리오 리스크 화면에서 섹터 집중도를 계산하기 위한 최소 sector membership을 제공한다.
전체 GICS universe가 아니라 현재 운영 후보와 core smoke 대상 심볼만 포함한다.

`0006_benchmark_composition_seed.sql`는 유료 provider 없이 drift 계산 경로를 검증하기 위한 `SPY` manual MVP 구성비다.
실제 운영 기준으로 쓰려면 dated provider holdings 또는 operator upload로 교체해야 하며, seed 값은 정확한 최신 ETF holdings라고 주장하지 않는다.
