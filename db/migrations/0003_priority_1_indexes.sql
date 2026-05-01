create index if not exists pipeline_run_kind_started_at_idx
    on ops.pipeline_run (run_kind, started_at desc);

create index if not exists pipeline_run_status_started_at_idx
    on ops.pipeline_run (status, started_at desc);

create index if not exists exchange_market_code_idx
    on ref.exchange (market_code);

create index if not exists instrument_issuer_id_idx
    on ref.instrument (issuer_id);

create index if not exists instrument_market_code_is_active_idx
    on ref.instrument (market_code, is_active);

create index if not exists classification_edge_parent_relation_idx
    on ref.classification_edge (parent_node_id, relation_type);

create index if not exists classification_edge_child_relation_idx
    on ref.classification_edge (child_node_id, relation_type);

create index if not exists source_document_data_source_id_idx
    on ingest.source_document (data_source_id);

create index if not exists source_document_ingested_by_run_id_idx
    on ingest.source_document (ingested_by_run_id);

create index if not exists source_document_published_at_idx
    on ingest.source_document (published_at desc);

create unique index if not exists source_document_external_document_uidx
    on ingest.source_document (data_source_id, external_document_id)
    where external_document_id is not null;

create index if not exists instrument_classification_membership_instrument_idx
    on ref.instrument_classification_membership (instrument_id, membership_type, valid_from desc);

create index if not exists instrument_classification_membership_node_idx
    on ref.instrument_classification_membership (node_id, membership_type, valid_from desc);

create index if not exists instrument_classification_membership_source_document_idx
    on ref.instrument_classification_membership (source_document_id);

create index if not exists daily_price_bar_trade_date_idx
    on market.daily_price_bar (trade_date desc);

create index if not exists daily_price_bar_source_run_id_idx
    on market.daily_price_bar (source_run_id);

create index if not exists financial_statement_period_instrument_period_end_idx
    on market.financial_statement_period (instrument_id, period_end desc);

create index if not exists financial_statement_period_source_document_id_idx
    on market.financial_statement_period (source_document_id);

create index if not exists financial_statement_period_source_run_id_idx
    on market.financial_statement_period (source_run_id);

create index if not exists financial_metric_value_metric_code_idx
    on market.financial_metric_value (metric_code);

create index if not exists financial_metric_value_source_run_id_idx
    on market.financial_metric_value (source_run_id);

create index if not exists estimate_snapshot_instrument_as_of_date_idx
    on market.estimate_snapshot (instrument_id, as_of_date desc, metric_code);

create index if not exists estimate_snapshot_source_run_id_idx
    on market.estimate_snapshot (source_run_id);

create unique index if not exists estimate_snapshot_identity_uidx
    on market.estimate_snapshot (
        instrument_id,
        as_of_date,
        fiscal_year,
        coalesce(fiscal_quarter, 0),
        metric_code
    );

create index if not exists macro_series_data_source_id_idx
    on macro.series (data_source_id);

create index if not exists macro_observation_observation_date_idx
    on macro.observation (observation_date desc);

create index if not exists macro_observation_source_run_id_idx
    on macro.observation (source_run_id);

create index if not exists event_event_type_event_at_idx
    on event.event (event_type, event_at desc);

create index if not exists event_event_created_by_run_id_idx
    on event.event (created_by_run_id);

create unique index if not exists event_dedupe_key_uidx
    on event.event (dedupe_key)
    where dedupe_key is not null;

create index if not exists event_document_link_document_id_idx
    on event.event_document_link (document_id);

create index if not exists event_instrument_impact_instrument_id_idx
    on event.event_instrument_impact (instrument_id, event_id);

create index if not exists event_classification_impact_node_id_idx
    on event.event_classification_impact (node_id, event_id);

create index if not exists cycle_state_snapshot_as_of_date_idx
    on signal.cycle_state_snapshot (as_of_date desc);

create index if not exists cycle_state_snapshot_source_run_id_idx
    on signal.cycle_state_snapshot (source_run_id);

create index if not exists investment_thesis_instrument_status_idx
    on signal.investment_thesis (instrument_id, status, created_at desc);

create index if not exists investment_thesis_primary_node_id_idx
    on signal.investment_thesis (primary_node_id);

create index if not exists investment_thesis_created_by_run_id_idx
    on signal.investment_thesis (created_by_run_id);

create index if not exists recommendation_batch_market_date_idx
    on signal.recommendation_batch (market_code, as_of_date desc);

create index if not exists recommendation_batch_source_run_id_idx
    on signal.recommendation_batch (source_run_id);

create unique index if not exists recommendation_batch_identity_uidx
    on signal.recommendation_batch (as_of_date, market_code, strategy_name, horizon_type);

create unique index if not exists recommendation_batch_rank_uidx
    on signal.recommendation (batch_id, rank_position);

create unique index if not exists recommendation_batch_instrument_uidx
    on signal.recommendation (batch_id, instrument_id);

create index if not exists recommendation_instrument_batch_idx
    on signal.recommendation (instrument_id, batch_id);

create index if not exists recommendation_thesis_id_idx
    on signal.recommendation (thesis_id);

create index if not exists portfolio_market_code_idx
    on portfolio.portfolio (market_code);

create index if not exists position_snapshot_portfolio_snapshot_date_idx
    on portfolio.position_snapshot (portfolio_id, snapshot_date desc);

create index if not exists position_snapshot_instrument_id_idx
    on portfolio.position_snapshot (instrument_id);

create index if not exists position_snapshot_linked_thesis_id_idx
    on portfolio.position_snapshot (linked_thesis_id);

create index if not exists position_snapshot_source_run_id_idx
    on portfolio.position_snapshot (source_run_id);
