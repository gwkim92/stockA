-- Disposable test schema: only the columns consumed by the production SELECT.
-- No production migration is run or modified. Every test rolls back this DDL.
create schema ref;
create schema market;
create schema signal;
create schema event;
create schema ingest;
create schema ai;
create table ref.instrument (instrument_id bigint primary key, primary_symbol text, name text, market_code text, currency_code text, is_active boolean);
create table market.financial_statement_period (period_id bigint, instrument_id bigint, statement_scope text, period_end date, report_date date, source_document_id bigint);
create table market.financial_metric_value (period_id bigint, metric_code text, metric_value numeric);
create table market.financial_metric_normalized (instrument_id bigint, metric_code text, metric_value numeric, metric_unit text, metric_status text, rationale text, statement_scope text, period_end date, as_of_date date, source_run_id bigint, period_id bigint);
create table ref.peer_group (peer_group_id bigint, group_code text, name text, methodology text);
create table market.peer_relative_snapshot (instrument_id bigint, peer_group_id bigint, metric_code text, instrument_value numeric, percentile_rank numeric, relative_signal text, as_of_date date, source_run_id bigint, peer_snapshot_id bigint);
create table market.valuation_snapshot (instrument_id bigint, method text, base_price numeric, fair_value_low numeric, fair_value_base numeric, fair_value_high numeric, margin_of_safety numeric, assumptions_json jsonb, confidence numeric, as_of_date date, source_run_id bigint, valuation_snapshot_id bigint);
create table signal.recommendation_batch (batch_id bigint, as_of_date date, strategy_name text, horizon_type text, source_run_id bigint);
create table signal.recommendation (recommendation_id bigint, batch_id bigint, instrument_id bigint, action text, bucket text, rank_position integer, total_score numeric, recommended_weight numeric, status text, thesis_id bigint);
create table signal.recommendation_score_component (recommendation_id bigint, component_name text, component_score numeric, component_weight numeric, explanation text);
create table signal.investment_thesis (thesis_id bigint, instrument_id bigint, title text, summary text, status text, conviction_score numeric, expected_holding_days integer, benchmark_code text, entry_conditions text, invalidation_conditions text, exit_conditions text, created_by_run_id bigint, created_at timestamptz, closed_at timestamptz);
create table event.event (event_id bigint, title text, summary text, event_at timestamptz, confidence numeric);
create table event.event_instrument_impact (event_id bigint, instrument_id bigint, impact_direction text, impact_strength numeric, confidence numeric, rationale text);
create table event.event_document_link (event_id bigint, document_id bigint, link_type text);
create table ingest.source_document (document_id bigint, korean_title text, korean_summary text, translation_confidence numeric, url text);
create table ref.classification_node (node_id bigint, code text, name text);
create table ref.instrument_classification_membership (instrument_id bigint, node_id bigint, valid_from date, valid_to date, confidence numeric);
create table ai.cycle_community_summary (node_id bigint, summary_type text, summary_json jsonb, as_of_date date, source_run_id bigint, updated_at timestamptz);
insert into ref.instrument values (101, 'AAPL', 'Synthetic company A', 'TEST', 'USD', true), (102, 'MSFT', 'Synthetic company B', 'TEST', 'USD', true);
insert into signal.recommendation_batch values (1, '2026-09-05', 'synthetic', 'long', null);
insert into signal.recommendation (recommendation_id,batch_id,instrument_id,thesis_id) values (1,1,101,900);
insert into signal.investment_thesis (thesis_id,instrument_id,title,summary,status,created_at) values
(10,101,'eligible oldest','fixture older','active','2026-09-01T00:00:00Z'),
(20,101,'eligible newest','fixture newest','closed','2026-09-05T23:59:59.999999Z'),
(900,101,'future linked','must not enter prior day','active','2026-09-06T00:00:00Z'),
(999,102,'another company','must not join','active','2026-09-05T23:59:59.999999Z');
insert into event.event values
(1,'start day','fixture','2026-09-05T00:00:00Z',0),
(2,'middle day','fixture','2026-09-05T18:00:00Z',0),
(3,'last microsecond','fixture','2026-09-05T23:59:59.999999Z',0),
(4,'next midnight','fixture','2026-09-06T00:00:00Z',0),
(5,'next morning','fixture','2026-09-06T03:00:00Z',0);
insert into event.event_instrument_impact (event_id,instrument_id) select event_id,101 from event.event;
insert into ingest.source_document values (1001,'eligible source','synthetic',0,null),(1004,'future source','synthetic',0,null);
insert into event.event_document_link values (3,1001,'source'),(4,1004,'source');
