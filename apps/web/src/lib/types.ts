export type ApiResponse<TData> = {
  contract_version: string;
  generated_at: string;
  data: TData;
  links: Record<string, string>;
};

export type RiskLevel = "low" | "medium" | "high";

export type DailyCockpitData = {
  as_of_date: string;
  portfolio_name: string;
  run_status: {
    daily_automation: string;
    latest_run_id: string;
    scheduler: string;
    holiday_skip: {
      enabled: boolean;
      source: string;
      would_skip_today: boolean;
    };
  };
  attention_summary: {
    open_ticket_count: number;
    critical_blind_spot_count: number;
    failed_pipeline_count: number;
    missing_thesis_count: number;
    missing_outcome_count: number;
  };
  top_actions: Array<{
    rank: number;
    symbol: string;
    action: string;
    reason: string;
    suggested_runner: string;
    risk_level: RiskLevel;
  }>;
  latest_metrics: {
    covered_weight: number;
    missing_thesis_weight: number;
    cash_weight: number;
    weight_coverage_ratio: number;
  };
};

export type RemediationTicketsData = {
  portfolio_name: string;
  status_filter: string;
  ticket_count: number;
  status_counts: Record<string, number>;
  tickets: Array<{
    ticket_id: string;
    symbol: string;
    instrument_id: string;
    status: string;
    action: string;
    remediation_type: string;
    suggested_runner: string;
    reason: string;
    risk_level: RiskLevel;
    source_review_item_id: string;
    source_run_id: string;
    created_at: string;
    updated_at: string;
    required_human_decision: string;
  }>;
};

export type DataHealthData = {
  overall_status: string;
  as_of_date: string;
  pipeline_runs: Array<{
    pipeline_name: string;
    latest_status: string;
    latest_run_id: string;
    finished_at: string;
  }>;
  scheduler: {
    install_status: string;
    runtime_env_readiness: string;
    holiday_skip_mode: string;
    latest_artifact_root: string;
  };
  freshness: Array<{
    dataset: string;
    status: string;
    latest_observation_date: string;
  }>;
  open_gates: string[];
};

export type CycleStateListData = {
  as_of_date: string;
  strategy_name: string;
  horizon_type: string;
  universe_version: string;
  cycle_states: Array<{
    theme_key: string;
    theme_name: string;
    state: string;
    previous_state: string;
    confidence: number;
    instrument_count: number;
    top_symbols: string[];
    features: {
      event_intensity: number | null;
      price_momentum: number | null;
      fundamental_quality: number | null;
    };
  }>;
};

export type RecommendationDetailData = {
  recommendation_id: string;
  symbol: string;
  instrument_id: string;
  as_of_date: string;
  strategy_name: string;
  horizon_type: string;
  recommendation: string;
  score: number;
  score_version: string;
  score_components: Array<{
    component: string;
    value: number;
    weight: number;
    evidence_id: string;
  }>;
  linked_thesis_id: string;
  outcome: {
    measurement_end_date: string;
    absolute_return: number;
    benchmark_return: number;
    alpha: number;
    label: string;
  };
};

export type ThesisDetailData = {
  thesis_id: string;
  symbol: string;
  instrument_id: string;
  status: string;
  thesis_version: string;
  created_from_recommendation_id: string;
  summary: string;
  core_claims: string[];
  invalidation_conditions: Array<{
    condition: string;
    current_status: string;
  }>;
  latest_review: {
    review_id: string;
    action: string;
    risk_level: RiskLevel;
    reviewed_at: string;
  };
  evidence: Array<{
    evidence_id: string;
    type: string;
    title: string;
  }>;
};

export type PortfolioCoverageData = {
  portfolio_name: string;
  as_of_date: string;
  strategy_name: string;
  coverage_measurement_end_date: string;
  summary: {
    position_count: number;
    covered_position_count: number;
    missing_thesis_count: number;
    missing_outcome_count: number;
    covered_weight: number;
    missing_thesis_weight: number;
    cash_weight: number;
    weight_coverage_ratio: number;
  };
  positions: Array<{
    symbol: string;
    instrument_id: string;
    weight: number;
    coverage_status: string;
    active_thesis_id: string | null;
    outcome_status: string;
    action: string;
  }>;
  attribution_readiness: {
    is_ready: boolean;
    blocking_reasons: string[];
  };
};

export type AiEvidenceDetailData = {
  evidence_id: string;
  title: string;
  evidence_type: string;
  event_at: string;
  instrument: {
    symbol: string;
    instrument_id: string;
  };
  source_document_id: string;
  classification: {
    theme_key: string;
    theme_name: string;
    impact_direction: string;
    impact_score: number;
  };
  extraction_run: {
    run_id: string;
    status: string;
    provider: string;
    model_id: string;
    prompt_version: string;
    finished_at: string;
    input_tokens: number;
    output_tokens: number;
    estimated_cost_usd: number;
    quality_gate: string;
  };
  extracted_fields: Array<{
    field: string;
    value: string;
    confidence: number;
    source_chunk_id: string;
  }>;
  source_chunks: Array<{
    chunk_id: string;
    section: string;
    locator: string;
    summary: string;
    relevance: string;
  }>;
  audit_notes: string[];
};

export type SourceDocumentDetailData = {
  document_id: string;
  title: string;
  source_type: string;
  publisher: string;
  symbol: string;
  cik: string;
  form_type: string;
  period_end: string;
  filed_at: string;
  accession_id: string;
  storage_uri: string;
  checksum: string;
  retrieval: {
    source_run_id: string;
    fetched_at: string;
    parser_version: string;
  };
  excerpts: Array<{
    chunk_id: string;
    section: string;
    locator: string;
    summary: string;
  }>;
  linked_evidence: Array<{
    evidence_id: string;
    evidence_type: string;
    title: string;
  }>;
  access_policy: {
    browser_download_enabled: boolean;
    reason: string;
  };
};

export type EventListData = {
  as_of_date: string;
  filters: {
    theme_key: string | null;
    symbol: string | null;
    event_type: string;
  };
  summary: {
    event_count: number;
    ai_extracted_count: number;
    source_document_count: number;
    themes_represented: number;
  };
  events: Array<{
    event_id: string;
    title: string;
    event_type: string;
    event_at: string;
    symbol: string;
    instrument_id: string;
    theme_key: string;
    theme_name: string;
    impact_direction: string;
    impact_score: number;
    source_document_id: string | null;
    ai_evidence_id: string | null;
    quality_gate: string;
  }>;
};

export type ThemeDetailData = {
  theme_key: string;
  theme_name: string;
  as_of_date: string;
  strategy_name: string;
  horizon_type: string;
  state: string;
  previous_state: string;
  confidence: number;
  cycle_score: number;
  cycle_history: Array<{
    as_of_date: string;
    state: string;
    confidence: number;
  }>;
  features: {
    event_intensity: number | null;
    price_momentum: number | null;
    fundamental_quality: number | null;
  };
  linked_instruments: Array<{
    symbol: string;
    instrument_id: string;
    membership_strength: number;
    active_thesis_id: string | null;
    latest_recommendation_id: string | null;
  }>;
  supporting_events: Array<{
    event_id: string;
    title: string;
    event_at: string;
    symbol: string;
    impact_direction: string;
    impact_score: number;
    ai_evidence_id: string | null;
    source_document_id: string | null;
  }>;
  operator_notes: string[];
};
