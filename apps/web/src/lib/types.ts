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
