# Database Schema Design

## Goal

이 문서는 섹터/테마 사이클 기반 중장기 투자 운영 시스템을 구현하기 위한 데이터 저장 구조를 고정한다.

목표는 아래 3가지를 동시에 만족하는 것이다.

1. 시장과 문서 데이터를 지속적으로 적재할 수 있어야 한다.
2. 추천 당시 판단 근거와 이후 검토 결과를 재구성할 수 있어야 한다.
3. 백테스트, 페이퍼트레이딩, 성과 분석으로 이어질 수 있어야 한다.

## Scope And Assumptions

- canonical 운영 저장소는 `Postgres`를 기준으로 설계한다.
- 대규모 시계열 분석과 백테스트는 이후 `Parquet + DuckDB`를 보조 분석 스토어로 둔다.
- 초기 구현은 미국 대형주 중심을 임시 가정으로 두되, 스키마는 멀티마켓을 지원한다.
- 초기 시간축은 `일봉` 중심이다.
- 실거래 자동화는 제외하고, 추천/검토/페이퍼 포트폴리오 관점으로 설계한다.

## Primary Key Strategy

구현용 DDL에서는 Postgres best practice에 맞춰 아래 원칙을 쓴다.

- 내부 surrogate key는 가능한 한 `bigint generated always as identity`
- 시계열 또는 junction 성격이 강한 테이블은 composite primary key
- 외부 연동 식별자는 별도 natural key 또는 unique index로 유지

즉 이 문서에서 초기 설명에 `uuid`로 표현했던 개념적 식별자는 실제 migration 단계에서 `bigint identity`와 composite key로 구체화할 수 있다.

## Core Design Principles

### 1. Canonical State First

추천, thesis, cycle state, review 결과는 모두 다시 읽을 수 있는 canonical 테이블에 저장한다.
LLM 출력도 최종 판단이 아니라 `추출 결과`와 `정규화 결과`로 분리 저장한다.

### 2. Stable Tables For Stable Concepts

아래처럼 구조가 안정적인 개념은 JSONB로 뭉개지지 않는다.

- 종목
- 테마/섹터 노드
- 가격
- 거시 시계열
- 이벤트
- thesis
- recommendation
- portfolio snapshot

JSONB는 아래 용도로만 제한한다.

- 모델 추출 원문
- 계산 근거 세부값
- 유연한 provenance
- 실험적 feature evidence

### 3. Provenance Everywhere

파이프라인이 만든 파생 결과는 가능한 한 `run_id`를 남긴다.
나중에 "이 점수는 어떤 코드와 어떤 입력으로 만들어졌나"를 추적할 수 있어야 한다.

### 4. Separate Current View And History

현재 상태만 덮어쓰면 안 된다.

- 분류 변경 이력
- 테마 membership 변화
- cycle state 변화
- thesis review 변화
- recommendation batch 변화

는 모두 시간축을 따라 남겨야 한다.

### 5. Multi-Market Ready, MVP Narrow

스키마는 멀티마켓을 지원하되, MVP 운영은 한 시장으로 제한한다.
즉 스키마는 범용적으로, 초기 데이터 적재는 좁게 간다.

## Storage Topology

### Canonical Operational Store: Postgres

아래 데이터를 저장한다.

- 기준정보
- 시장 시계열
- 문서 메타데이터
- 이벤트 정규화 결과
- 사이클 상태
- thesis
- recommendation
- 포트폴리오/리뷰/성과
- 파이프라인 provenance

### Analytical Research Store: Parquet + DuckDB

아래 데이터를 보조 저장한다.

- 대량 feature matrix
- 백테스트용 조인 결과
- 팩터 실험 산출물
- 모델 실험 결과

중요한 원칙:

- 추천과 thesis의 source of truth는 Postgres다.
- 대량 계산용 wide table은 Parquet/DuckDB로 흘려도 된다.
- 분석 결과가 운영 상태를 바꾸면 최종 결과만 다시 Postgres에 반영한다.

### Raw Artifact Store

원문 HTML, PDF, transcript, 대량 뉴스 본문은 파일/object storage 경로를 저장하고, Postgres에는 메타데이터와 포인터만 둔다.

## Database Schemas

권장 Postgres schema 구분:

- `ref`
- `ingest`
- `market`
- `macro`
- `event`
- `signal`
- `portfolio`
- `performance`
- `ops`
- `ai`

## ai Schema

AI 계층은 추천 결정을 직접 저장하는 곳이 아니라 model call, prompt, chunk, embedding pointer, extraction artifact, eval 결과를 감사 가능하게 남기는 schema다.

초기 migration은 `db/migrations/0005_ai_intelligence.sql`이다.

### `ai.prompt_template`

- `template_id bigint pk`
- `template_name text`
- `template_version text`
- `system_purpose text`
- `template_text text`
- `output_schema_json jsonb`
- `is_active boolean`
- `created_at timestamptz`

역할:

- task별 prompt와 output schema version을 고정한다.
- prompt가 바뀌면 extraction result와 eval result를 다시 비교할 수 있게 한다.

### `ai.model_invocation`

- `invocation_id bigint pk`
- `run_id bigint fk -> ops.pipeline_run.run_id`
- `task_name text`
- `provider text`
- `model_name text`
- `reasoning_effort text`
- `prompt_template_id bigint fk -> ai.prompt_template.template_id`
- `input_token_count integer`
- `output_token_count integer`
- `cached_input_token_count integer`
- `estimated_cost_usd numeric`
- `latency_ms integer`
- `status text`
- `error_summary text`
- `request_hash text`
- `created_at timestamptz`

역할:

- token/cost/latency/status를 task별로 추적한다.
- prompt caching 효과와 model routing 비용을 측정한다.

### `ai.document_chunk`

- `chunk_id bigint pk`
- `document_id bigint fk -> ingest.source_document.document_id`
- `chunk_index integer`
- `content_hash text`
- `text_preview text`
- `token_count integer`
- `chunk_metadata jsonb`
- `created_at timestamptz`

역할:

- raw document를 bounded context로 나누기 위한 metadata를 저장한다.
- Postgres에는 full text를 넣지 않고 preview, hash, metadata, pointer만 둔다.

### `ai.embedding_index`

- `embedding_id bigint pk`
- `chunk_id bigint fk -> ai.document_chunk.chunk_id`
- `provider text`
- `model_name text`
- `embedding_dimension integer`
- `vector_storage_uri text`
- `content_hash text`
- `created_at timestamptz`

역할:

- vector backend를 아직 고정하지 않고 adapter URI로 연결한다.
- pgvector, OpenAI vector store, external vector DB로 갈아탈 수 있게 한다.

### `ai.extraction_artifact`

- `artifact_id bigint pk`
- `invocation_id bigint fk -> ai.model_invocation.invocation_id`
- `document_id bigint fk -> ingest.source_document.document_id`
- `event_id bigint fk -> event.event.event_id`
- `artifact_type text`
- `output_json jsonb`
- `confidence numeric`
- `created_at timestamptz`

역할:

- LLM output을 canonical writer 이전 또는 함께 저장한다.
- validator 실패 output도 감사와 eval 개선에 사용할 수 있게 한다.

### `ai.eval_run`

- `eval_run_id bigint pk`
- `eval_name text`
- `dataset_version text`
- `provider text`
- `model_name text`
- `prompt_template_id bigint fk -> ai.prompt_template.template_id`
- `score_json jsonb`
- `created_at timestamptz`

역할:

- prompt/model/schema 변경 전후 품질을 비교한다.
- 추천 전 단계인 event extraction, theme mapping, thesis review 품질을 회귀 테스트한다.

## ref Schema

기준정보와 분류 체계를 저장한다.

### `ref.market`

- `market_code text pk`
- `name text`
- `country_code text`
- `currency_code text`
- `timezone text`
- `is_active boolean`

역할:

- 미국, 한국 등 거래 시장 단위 관리

### `ref.exchange`

- `exchange_id uuid pk`
- `market_code text fk -> ref.market.market_code`
- `mic_code text unique`
- `name text`
- `timezone text`
- `is_primary boolean`

역할:

- NASDAQ, NYSE, KRX 같은 거래소 관리

### `ref.issuer`

- `issuer_id uuid pk`
- `legal_name text`
- `display_name text`
- `country_code text`
- `issuer_type text`
- `created_at timestamptz`

역할:

- 법인 단위 엔터티 저장

### `ref.instrument`

- `instrument_id uuid pk`
- `issuer_id uuid fk -> ref.issuer.issuer_id`
- `exchange_id uuid fk -> ref.exchange.exchange_id`
- `market_code text fk -> ref.market.market_code`
- `primary_symbol text`
- `instrument_type text`
- `currency_code text`
- `name text`
- `is_active boolean`
- `listed_at timestamptz`
- `delisted_at timestamptz null`

권장 unique:

- `(exchange_id, primary_symbol)` active row 기준

역할:

- 주식, ETF, 지수, ADR 등 거래 대상 기준 테이블

### `ref.instrument_alias`

- `alias_id uuid pk`
- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `alias_type text`
- `alias_value text`
- `source_name text`
- `valid_from date`
- `valid_to date null`

예시 `alias_type`:

- ticker
- isin
- cusip
- sedol
- vendor_symbol

### `ref.classification_node`

- `node_id uuid pk`
- `taxonomy_family text`
- `node_type text`
- `code text`
- `name text`
- `description text`
- `status text`

예시:

- `taxonomy_family`: `gics`, `internal_theme`, `internal_sector`
- `node_type`: `sector`, `industry_group`, `industry`, `sub_industry`, `theme`, `subtheme`

핵심 결정:

- 섹터, 산업, 테마를 별도 테이블로 찢지 않고 `classification_node`로 통합한다.
- cycle engine은 이 `node_id`를 기준으로 돌린다.

### `ref.classification_edge`

- `edge_id uuid pk`
- `parent_node_id uuid fk -> ref.classification_node.node_id`
- `child_node_id uuid fk -> ref.classification_node.node_id`
- `relation_type text`
- `weight numeric(10,4) null`
- `valid_from date`
- `valid_to date null`

예시 `relation_type`:

- hierarchy
- depends_on
- benefits_from
- negatively_correlated_with
- supplier_to

역할:

- 단순 계층뿐 아니라 테마 간 인과/공급망 관계 저장

### `ref.instrument_classification_membership`

- `membership_id uuid pk`
- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `node_id uuid fk -> ref.classification_node.node_id`
- `membership_type text`
- `confidence numeric(5,4)`
- `source_document_id uuid null`
- `valid_from date`
- `valid_to date null`

예시 `membership_type`:

- primary_sector
- primary_industry
- direct_theme
- derived_theme
- watch_theme

현재 bootstrap 구현은 `docs/instrument-theme-enrichment.md`를 기준으로 selected strategy universe instruments에 대해 `derived_theme` memberships를 만든다.
초기 입력은 `event.event_instrument_impact`와 `event.event_classification_impact`의 교집합이다.

## ingest Schema

원문과 수집 provenance를 저장한다.

### `ingest.data_source`

- `data_source_id uuid pk`
- `source_name text unique`
- `source_kind text`
- `base_url text null`
- `license_type text null`
- `trust_score numeric(5,4) null`
- `is_active boolean`

예시 `source_kind`:

- market_data
- filings
- news
- macro
- manual

### `ingest.source_document`

- `document_id uuid pk`
- `data_source_id uuid fk -> ingest.data_source.data_source_id`
- `external_document_id text null`
- `document_type text`
- `title text`
- `summary text null`
- `url text null`
- `language text null`
- `published_at timestamptz`
- `ingested_at timestamptz`
- `raw_storage_uri text null`
- `checksum text null`
- `ingested_by_run_id uuid fk -> ops.pipeline_run.run_id`

예시 `document_type`:

- news
- filing
- earnings_call
- policy_release
- research_report
- transcript

### `ingest.document_extraction`

- `extraction_id uuid pk`
- `document_id uuid fk -> ingest.source_document.document_id`
- `model_run_id uuid fk -> ops.model_run.model_run_id`
- `extraction_kind text`
- `schema_version text`
- `output_json jsonb`
- `confidence numeric(5,4) null`
- `created_at timestamptz`

예시 `extraction_kind`:

- summary
- entity_tagging
- event_candidate
- theme_tagging
- sentiment

역할:

- LLM이 뽑아낸 구조화 결과의 원본 저장
- 이후 `event` 테이블은 여기서 정규화된 결과만 반영

## market Schema

정형 시장 데이터를 저장한다.

### `market.daily_price_bar`

- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `trade_date date`
- `open numeric(18,6)`
- `high numeric(18,6)`
- `low numeric(18,6)`
- `close numeric(18,6)`
- `adjusted_close numeric(18,6)`
- `volume bigint`
- `turnover_value numeric(20,2) null`
- `market_cap numeric(20,2) null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

pk:

- `(instrument_id, trade_date)`

### `market.corporate_action`

- `corporate_action_id uuid pk`
- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `action_type text`
- `announced_at timestamptz null`
- `ex_date date null`
- `effective_date date null`
- `ratio numeric(18,8) null`
- `cash_amount numeric(18,6) null`
- `currency_code text null`
- `source_document_id uuid null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`

예시 `action_type`:

- dividend
- split
- reverse_split
- rights_issue
- delisting

### `market.financial_statement_period`

- `period_id uuid pk`
- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `statement_scope text`
- `fiscal_year int`
- `fiscal_quarter int null`
- `period_start date`
- `period_end date`
- `report_date date null`
- `currency_code text`
- `is_audited boolean`
- `source_document_id uuid null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`

예시 `statement_scope`:

- annual
- quarterly
- ttm

### `market.financial_metric_value`

- `period_id uuid fk -> market.financial_statement_period.period_id`
- `metric_code text`
- `metric_value numeric(24,6)`
- `unit text`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`

pk:

- `(period_id, metric_code)`

예시 `metric_code`:

- revenue
- gross_profit
- operating_income
- net_income
- eps_basic
- fcf
- debt_to_equity
- roa
- roe

핵심 결정:

- 재무 데이터를 wide table 하나로 박아 넣지 않고, period + metric value 구조로 간다.
- 초기 metric set이 자주 바뀌는 단계에서 유지보수가 쉽다.

### `market.estimate_snapshot`

- `estimate_snapshot_id uuid pk`
- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `as_of_date date`
- `fiscal_year int`
- `fiscal_quarter int null`
- `metric_code text`
- `mean_value numeric(24,6) null`
- `median_value numeric(24,6) null`
- `high_value numeric(24,6) null`
- `low_value numeric(24,6) null`
- `analyst_count int null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`

역할:

- EPS, 매출 추정치 변화 저장

### `market.investor_flow_daily`

- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `trade_date date`
- `investor_type text`
- `net_buy_value numeric(20,2) null`
- `net_buy_volume bigint null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`

pk:

- `(instrument_id, trade_date, investor_type)`

예시 `investor_type`:

- foreign
- institution
- retail
- fund

## macro Schema

거시 지표와 상위 시장 변수를 저장한다.

### `macro.series`

- `series_id uuid pk`
- `series_code text unique`
- `name text`
- `category text`
- `frequency text`
- `unit text`
- `region_code text`
- `data_source_id uuid fk -> ingest.data_source.data_source_id`
- `is_active boolean`

예시 `category`:

- policy_rate
- inflation
- labor
- growth
- liquidity
- fx
- commodity
- bond_yield

### `macro.observation`

- `series_id uuid fk -> macro.series.series_id`
- `observation_date date`
- `value numeric(24,8)`
- `released_at timestamptz null`
- `revision_number int default 0`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`

pk:

- `(series_id, observation_date, revision_number)`

## event Schema

문서에서 추출된 사건과 영향 관계를 저장한다.

### `event.event`

- `event_id uuid pk`
- `event_type text`
- `title text`
- `summary text`
- `event_at timestamptz`
- `detected_at timestamptz`
- `time_horizon text`
- `impact_polarity text`
- `significance_score numeric(5,4)`
- `confidence numeric(5,4)`
- `dedupe_key text null`
- `created_by_run_id uuid fk -> ops.pipeline_run.run_id`

예시 `event_type`:

- earnings_surprise
- policy_support
- policy_restriction
- capex_expansion
- supply_shortage
- geopolitical_risk
- product_launch
- mna

### `event.event_document_link`

- `event_id uuid fk -> event.event.event_id`
- `document_id uuid fk -> ingest.source_document.document_id`
- `link_type text`

pk:

- `(event_id, document_id, link_type)`

예시 `link_type`:

- primary
- supporting
- contradiction

### `event.event_instrument_impact`

- `event_id uuid fk -> event.event.event_id`
- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `impact_direction text`
- `impact_strength numeric(5,4)`
- `confidence numeric(5,4)`
- `rationale text null`

pk:

- `(event_id, instrument_id)`

### `event.event_classification_impact`

- `event_id uuid fk -> event.event.event_id`
- `node_id uuid fk -> ref.classification_node.node_id`
- `impact_direction text`
- `impact_strength numeric(5,4)`
- `confidence numeric(5,4)`
- `rationale text null`

pk:

- `(event_id, node_id)`

핵심 결정:

- polymorphic generic target 테이블 대신 `instrument impact`, `classification impact`를 분리한다.
- 관계형 무결성을 더 강하게 유지한다.

## signal Schema

파생 feature, cycle state, thesis, recommendation을 저장한다.

### `signal.feature_definition`

- `feature_code text pk`
- `subject_kind text`
- `feature_name text`
- `description text`
- `value_type text`
- `default_horizon text null`
- `owner text null`
- `is_active boolean`

예시 `subject_kind`:

- instrument
- classification

### `signal.instrument_feature_value`

- `instrument_id uuid fk -> ref.instrument.instrument_id`
- `as_of_date date`
- `feature_code text fk -> signal.feature_definition.feature_code`
- `feature_value numeric(24,8) null`
- `feature_text text null`
- `zscore numeric(24,8) null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`
- `evidence_json jsonb null`

pk:

- `(instrument_id, as_of_date, feature_code)`

현재 bootstrap migration은 `db/migrations/0006_market_feature_snapshot.sql`에서 이 테이블을 실제 구현한다.
초기 운영 경로는 instrument features만 사용한다.

### `signal.classification_feature_value`

- `node_id uuid fk -> ref.classification_node.node_id`
- `as_of_date date`
- `feature_code text fk -> signal.feature_definition.feature_code`
- `feature_value numeric(24,8) null`
- `feature_text text null`
- `zscore numeric(24,8) null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`
- `evidence_json jsonb null`

pk:

- `(node_id, as_of_date, feature_code)`

이 테이블은 아직 migration으로 구현하지 않았다.
현재 cycle snapshot bootstrap은 이 테이블 없이 `signal.cycle_state_snapshot`의 component score와 `evidence_json`을 먼저 채운다.

### `signal.cycle_state_snapshot`

- `node_id uuid fk -> ref.classification_node.node_id`
- `as_of_date date`
- `cycle_state text`
- `cycle_score numeric(6,4)`
- `trend_score numeric(6,4) null`
- `earnings_revision_score numeric(6,4) null`
- `liquidity_score numeric(6,4) null`
- `valuation_score numeric(6,4) null`
- `event_heat_score numeric(6,4) null`
- `breadth_score numeric(6,4) null`
- `source_run_id uuid fk -> ops.pipeline_run.run_id`
- `evidence_json jsonb null`

pk:

- `(node_id, as_of_date)`

예시 `cycle_state`:

- forming
- expanding
- confirming
- overheating
- correcting
- basing
- reaccelerating
- structurally_broken

현재 bootstrap 구현은 `docs/cycle-state-snapshot.md`에 정리되어 있다.
입력은 `ref.instrument_classification_membership`, `signal.instrument_feature_value`, recent `event.* impact`이고 direct internal theme node만 계산한다.

### `signal.investment_thesis`

- `thesis_id bigint pk`
- `instrument_id bigint fk -> ref.instrument.instrument_id`
- `primary_node_id bigint null fk -> ref.classification_node.node_id`
- `thesis_type text`
- `title text`
- `summary text`
- `status text`
- `conviction_score numeric(6,4) null`
- `expected_holding_days int null`
- `benchmark_code text null`
- `entry_conditions text null`
- `invalidation_conditions text`
- `exit_conditions text null`
- `created_at timestamptz`
- `closed_at timestamptz null`
- `created_by_run_id bigint fk -> ops.pipeline_run.run_id`

예시 `thesis_type`:

- long_term_core
- medium_term_cycle
- watchlist

예시 `status`:

- active
- paused
- invalidated
- closed

현재 bootstrap 구현은 `docs/thesis-bootstrap.md`에 정리되어 있다.
초기 thesis는 active recommendation row를 입력으로 하는 deterministic template이며, 같은 `instrument_id`, `primary_node_id`, `thesis_type`의 active thesis를 갱신하거나 새로 생성한다.

### `signal.thesis_factor`

- `thesis_factor_id uuid pk`
- `thesis_id uuid fk -> signal.investment_thesis.thesis_id`
- `factor_type text`
- `factor_label text`
- `linked_node_id uuid null fk -> ref.classification_node.node_id`
- `direction text`
- `weight numeric(6,4) null`
- `evidence_json jsonb null`

역할:

- thesis의 근거를 구조화해 나중에 review와 attribution에 연결

### `signal.thesis_review`

- `review_id bigint pk`
- `thesis_id bigint fk -> signal.investment_thesis.thesis_id`
- `review_date date`
- `review_source text`
- `action text`
- `health_score numeric(6,4) null`
- `summary text`
- `change_notes text null`
- `next_review_date date null`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

예시 `action`:

- keep
- add
- reduce
- exit
- watch

현재 bootstrap 구현은 `docs/thesis-review-bootstrap.md`에 정리되어 있다.
초기 review는 linked active recommendation/thesis를 입력으로 하는 deterministic rule이며, `(thesis_id, review_date, review_source)` 기준으로 갱신 또는 생성한다.

### `signal.strategy_universe_batch`

- `universe_batch_id bigint pk`
- `as_of_date date`
- `market_code text fk -> ref.market.market_code`
- `strategy_name text`
- `horizon_type text`
- `universe_version text`
- `selection_rule text`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

역할:

- recommendation 이전의 전략별 investable universe snapshot을 저장한다.
- canonical universe 전체와 실제 평가 대상 universe를 분리한다.

identity:

- `(as_of_date, market_code, strategy_name, horizon_type, universe_version)`

### `signal.strategy_universe_member`

- `universe_batch_id bigint fk -> signal.strategy_universe_batch.universe_batch_id`
- `instrument_id bigint fk -> ref.instrument.instrument_id`
- `rank_position int`
- `selection_score numeric(10,4)`
- `latest_trade_date date`
- `latest_adjusted_close numeric(18,6)`
- `observation_count int`
- `inclusion_reason text`

pk:

- `(universe_batch_id, instrument_id)`

역할:

- 특정 strategy universe snapshot의 구성 종목과 선택 근거를 저장한다.
- 초기 구현은 price availability 기반 deterministic slicing만 사용한다.

### `signal.recommendation_batch`

- `batch_id bigint pk`
- `as_of_date date`
- `market_code text fk -> ref.market.market_code`
- `strategy_name text`
- `horizon_type text`
- `universe_version text null`
- `notes text null`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

### `signal.recommendation`

- `recommendation_id bigint pk`
- `batch_id bigint fk -> signal.recommendation_batch.batch_id`
- `instrument_id bigint fk -> ref.instrument.instrument_id`
- `thesis_id bigint null fk -> signal.investment_thesis.thesis_id`
- `bucket text`
- `action text`
- `rank_position int`
- `total_score numeric(8,4)`
- `recommended_weight numeric(8,4) null`
- `status text`

예시 `bucket`:

- core
- cycle
- watch
- avoid

현재 bootstrap 구현은 `docs/recommendation-bootstrap.md`에 정리되어 있다.
초기 recommendation row는 direct internal theme/cycle evidence가 있는 selected universe instruments만 대상으로 하며, `thesis_id`는 `thesis-bootstrap` 이후 채워진다.

### `signal.recommendation_score_component`

- `recommendation_id bigint fk -> signal.recommendation.recommendation_id`
- `component_name text`
- `component_score numeric(8,4)`
- `component_weight numeric(8,4) null`
- `explanation text null`
- `created_at timestamptz`

pk:

- `(recommendation_id, component_name)`

현재 bootstrap 구현은 `docs/recommendation-score-component.md`에 정리되어 있다.
초기 component는 `cycle_score`, `momentum_score`, `short_term_score`, `rank_score` 네 가지이며, `recommendation-bootstrap` transaction 안에서 recommendation child rows로 저장한다.

## portfolio Schema

페이퍼 포트폴리오와 운용 판단을 저장한다.

### `portfolio.portfolio`

- `portfolio_id bigint pk`
- `portfolio_name text`
- `base_currency text`
- `market_code text fk -> ref.market.market_code`
- `strategy_name text`
- `is_paper boolean`
- `created_at timestamptz`

### `portfolio.position_snapshot`

- `portfolio_id bigint fk -> portfolio.portfolio.portfolio_id`
- `instrument_id bigint fk -> ref.instrument.instrument_id`
- `snapshot_date date`
- `quantity numeric(24,8)`
- `cost_basis numeric(20,6) null`
- `market_price numeric(18,6)`
- `market_value numeric(20,2)`
- `weight numeric(8,4) null`
- `unrealized_pnl numeric(20,2) null`
- `linked_thesis_id bigint null fk -> signal.investment_thesis.thesis_id`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`

pk:

- `(portfolio_id, instrument_id, snapshot_date)`

현재 CSV upsert 구현은 `docs/position-snapshot-ingest.md`에 정리되어 있다.
초기 position snapshot ingest는 CSV symbol을 canonical `ref.instrument.primary_symbol`에 매핑하고, `linked_thesis_id`가 없으면 latest active thesis를 자동 연결한다.

### `portfolio.review`

- `portfolio_review_id bigint pk`
- `portfolio_id bigint fk -> portfolio.portfolio.portfolio_id`
- `review_date date`
- `review_source text`
- `overall_summary text`
- `cash_weight numeric(8,4) null`
- `risk_level text null`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

unique:

- `(portfolio_id, review_date, review_source)`

### `portfolio.review_item`

- `review_item_id bigint pk`
- `portfolio_review_id bigint fk -> portfolio.review.portfolio_review_id`
- `instrument_id bigint fk -> ref.instrument.instrument_id`
- `thesis_id bigint null fk -> signal.investment_thesis.thesis_id`
- `recommendation_id bigint null fk -> signal.recommendation.recommendation_id`
- `thesis_review_id bigint null fk -> signal.thesis_review.review_id`
- `action text`
- `reason text`
- `priority int null`
- `health_score numeric(6,4) null`
- `current_weight numeric(8,4) null`
- `recommended_weight numeric(8,4) null`
- `weight_gap numeric(8,4) null`
- `market_value numeric(20,2) null`
- `unrealized_pnl numeric(20,2) null`
- `created_at timestamptz`

unique:

- `(portfolio_review_id, instrument_id)`

현재 bootstrap 구현은 `docs/portfolio-review-bootstrap.md`에 정리되어 있다.
초기 portfolio review는 `portfolio.position_snapshot`을 읽고 thesis review action을 보유 검토 action으로 변환한다. trade/order 생성은 아직 없다.

### `portfolio.remediation_ticket`

- `remediation_ticket_id bigint pk`
- `portfolio_review_id bigint fk -> portfolio.review.portfolio_review_id`
- `instrument_id bigint fk -> ref.instrument.instrument_id`
- `action text`
- `remediation_type text`
- `suggested_runner text`
- `suggested_next_step text`
- `status text`
- `priority int null`
- `risk_level text null`
- `health_score numeric(6,4) null`
- `current_weight numeric(8,4) null`
- `recommended_weight numeric(8,4) null`
- `latest_reason text`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `opened_at timestamptz`
- `updated_at timestamptz`
- `last_seen_at timestamptz`
- `resolved_at timestamptz null`

unique:

- `(portfolio_review_id, instrument_id, action, remediation_type)`

현재 bootstrap 구현은 `docs/portfolio-remediation-ticket-bootstrap.md`에 정리되어 있다.
초기 remediation ticket은 portfolio review attention item을 persistent open ticket으로 저장한다. `portfolio.review_item`은 review rerun 때 delete/insert되므로 `review_item_id` FK는 두지 않는다.

## performance Schema

추천 이후 성과와 원인 분석을 저장한다.

### `performance.recommendation_outcome`

- `outcome_id bigint pk`
- `recommendation_id bigint fk -> signal.recommendation.recommendation_id`
- `measurement_start_date date`
- `measurement_end_date date`
- `horizon_days int`
- `entry_price numeric(18,6)`
- `exit_price numeric(18,6)`
- `absolute_return_pct numeric(12,6)`
- `benchmark_code text null`
- `benchmark_return_pct numeric(12,6) null`
- `alpha_pct numeric(12,6) null`
- `max_drawdown_pct numeric(12,6)`
- `outcome_label text`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

unique:

- `(recommendation_id, measurement_end_date)`

### `performance.thesis_outcome`

- `outcome_id bigint pk`
- `thesis_id bigint fk -> signal.investment_thesis.thesis_id`
- `recommendation_id bigint null fk -> signal.recommendation.recommendation_id`
- `measurement_start_date date`
- `measurement_end_date date`
- `status text`
- `holding_days int`
- `absolute_return_pct numeric(12,6)`
- `benchmark_code text null`
- `benchmark_return_pct numeric(12,6) null`
- `alpha_pct numeric(12,6) null`
- `success_grade text`
- `summary text`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

unique:

- `(thesis_id, measurement_end_date)`

현재 bootstrap 구현은 `docs/performance-outcome-bootstrap.md`에 정리되어 있다.
초기 performance outcome은 adjusted close 기반 사후 측정이다. 추천, thesis, portfolio review 판단을 직접 수정하지 않는다.

### `performance.attribution_run`

`0011_performance_attribution.sql`에 포함된다. 목표는 portfolio 성과를 security selection, sector/theme exposure, macro/cycle exposure, cash timing 등으로 분해하는 것이다.

필드:

- `attribution_run_id bigint pk`
- `portfolio_id bigint fk -> portfolio.portfolio.portfolio_id`
- `snapshot_date date`
- `measurement_start_date date`
- `measurement_end_date date`
- `methodology text`
- `source_run_id bigint fk -> ops.pipeline_run.run_id`
- `created_at timestamptz`

unique:

- `(portfolio_id, snapshot_date, measurement_end_date, methodology)`

### `performance.attribution_component`

`0011_performance_attribution.sql`에 포함된다.

필드:

- `attribution_component_id bigint pk`
- `attribution_run_id bigint fk -> performance.attribution_run.attribution_run_id`
- `component_type text`
- `component_key text`
- `instrument_id bigint null fk -> ref.instrument.instrument_id`
- `thesis_id bigint null fk -> signal.investment_thesis.thesis_id`
- `recommendation_id bigint null fk -> signal.recommendation.recommendation_id`
- `weight numeric(8,4) null`
- `return_pct numeric(12,6) null`
- `benchmark_return_pct numeric(12,6) null`
- `alpha_pct numeric(12,6) null`
- `contribution_bps numeric(12,4)`
- `summary text null`
- `created_at timestamptz`

unique:

- `(attribution_run_id, component_type, component_key)`

예시 `component_type`:

- security_selection
- sector_allocation
- theme_exposure
- macro_exposure
- cash_timing

현재 bootstrap 구현은 `docs/portfolio-attribution-bootstrap.md`에 정리되어 있다. v1은 `position_weighted_alpha_v1`이며, security/theme/cash component만 저장한다.

## ops Schema

파이프라인, 모델 실행, 변경 이력을 저장한다.

### `ops.pipeline_run`

- `run_id uuid pk`
- `run_kind text`
- `pipeline_name text`
- `code_version text null`
- `started_at timestamptz`
- `ended_at timestamptz null`
- `status text`
- `config_json jsonb null`
- `error_summary text null`

예시 `run_kind`:

- ingest
- extraction
- feature
- cycle
- thesis
- recommendation
- portfolio_review
- attribution
- backfill

### `ops.model_run`

- `model_run_id uuid pk`
- `run_id uuid fk -> ops.pipeline_run.run_id`
- `provider text`
- `model_name text`
- `prompt_version text null`
- `input_tokens int null`
- `output_tokens int null`
- `latency_ms int null`
- `estimated_cost_usd numeric(12,6) null`
- `metadata_json jsonb null`

### `ops.audit_log`

- `audit_id uuid pk`
- `entity_type text`
- `entity_id uuid`
- `change_type text`
- `changed_at timestamptz`
- `changed_by text`
- `change_payload jsonb`

역할:

- manual override, 중요 상태 변경, 추천 취소 같은 감사 로그 기록

## Key Relationships

핵심 흐름은 아래처럼 연결된다.

1. `source_document`에 원문이 들어온다.
2. `document_extraction`에 LLM 추출 결과를 저장한다.
3. 정규화된 사건은 `event`에 들어간다.
4. 사건 영향은 `event_instrument_impact`, `event_classification_impact`로 연결된다.
5. 테마/섹터 구조는 `classification_node`, `classification_edge`에 저장된다.
6. 사이클 결과는 `cycle_state_snapshot`에 기록된다.
7. 종목 thesis는 `investment_thesis`에 저장된다.
8. 추천 배치는 `recommendation_batch`, 개별 추천은 `recommendation`에 저장된다.
9. 실제 보유와 검토는 `portfolio.*`에 저장된다.
10. 추천 이후 성과는 `performance.*`에 저장된다.

## JSONB Usage Rules

JSONB 허용:

- `ingest.document_extraction.output_json`
- `signal.*_feature_value.evidence_json`
- `signal.cycle_state_snapshot.evidence_json`
- `signal.thesis_factor.evidence_json`
- `ops.pipeline_run.config_json`
- `ops.model_run.metadata_json`
- `ops.audit_log.change_payload`

JSONB 금지 대상:

- 가격 bar
- instrument 기준정보
- recommendation score 핵심 수치
- thesis status
- portfolio snapshot 핵심 수치

## Partitioning And Indexing Guidance

초기 구현부터 고려할 것:

- `market.daily_price_bar`: `trade_date` 기준 range partition
- `macro.observation`: `observation_date` 기준 range partition
- `signal.instrument_feature_value`, `signal.classification_feature_value`: `as_of_date` 기준 partition 고려
- `ingest.source_document`: `published_at` index
- `event.event`: `event_at`, `event_type` index
- `signal.recommendation`: `(batch_id, rank_position)` index
- `portfolio.position_snapshot`: `(portfolio_id, snapshot_date)` index

## MVP Table Set

처음부터 전부 만들 필요는 없다.

우선순위 1:

- `ref.market`
- `ref.exchange`
- `ref.issuer`
- `ref.instrument`
- `ref.classification_node`
- `ref.classification_edge`
- `ref.instrument_classification_membership`
- `ops.pipeline_run`
- `ingest.data_source`
- `ingest.source_document`
- `market.daily_price_bar`
- `market.financial_statement_period`
- `market.financial_metric_value`
- `market.estimate_snapshot`
- `macro.series`
- `macro.observation`
- `event.event`
- `event.event_document_link`
- `event.event_instrument_impact`
- `event.event_classification_impact`
- `signal.cycle_state_snapshot`
- `signal.investment_thesis`
- `signal.recommendation_batch`
- `signal.recommendation`
- `portfolio.portfolio`
- `portfolio.position_snapshot`

우선순위 2:

- `ingest.document_extraction`
- `market.investor_flow_daily`
- `signal.feature_definition`
- `signal.instrument_feature_value`
- `signal.classification_feature_value`
- `signal.thesis_factor`
- `signal.thesis_review`
- `signal.recommendation_score_component`
- `portfolio.trade`
- `portfolio.review`
- `portfolio.review_item`
- `portfolio.remediation_ticket`
- `performance.recommendation_outcome`
- `performance.thesis_outcome`
- `performance.attribution_run`
- `performance.attribution_component`

우선순위 3:

- `ops.model_run`
- `ops.audit_log`

## Deferred Decisions

아직 미정인 항목:

- 벤치마크를 `instrument`로만 처리할지 별도 benchmark table을 둘지
- 국가/정책 이벤트용 별도 엔터티 테이블을 둘지
- 대형 뉴스 코퍼스 full text 검색을 Postgres에서 처리할지 별도 검색 인덱스를 둘지
- embeddings를 DB에 저장할지 벡터 스토어로 분리할지

## Recommended Next Step

다음 구현 단계는 이 문서를 바탕으로 아래를 만드는 것이다.

1. 초기 instrument universe seed 또는 ingest bootstrap 구현
2. 첫 적재 대상 시장과 데이터 소스 고정
3. MVP 테이블 기준 ingest pipeline 순서 정의
4. priority 2 schema migration 범위 정의
