export type ApiResponse<TData> = {
  contract_version: string;
  generated_at: string;
  data: TData;
  pagination?: {
    limit: number;
    cursor: string | null;
    next_cursor: string | null;
    has_more: boolean;
    item_count: number;
  };
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
  allocation_policy: {
    policy_id: string;
    policy_name: string;
    status: string;
    policy_scope: string;
    max_single_position_weight: number | null;
    min_rebalance_target_weight: number | null;
    max_sector_weight: number | null;
    max_theme_weight: number | null;
    max_unclassified_weight: number | null;
    valid_from: string;
    valid_to: string;
    rationale: string;
  };
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
    job_id: string;
    domain: string;
    cadence: string;
    expected_after_local: string;
    stale_after_hours: number;
    artifact_policy: string;
    latest_status: string;
    health_status: string;
    latest_run_id: string;
    finished_at: string;
  }>;
  scheduler: {
    install_status: string;
    runtime_env_readiness: string;
    holiday_skip_mode: string;
    latest_artifact_root: string;
    activation: {
      status: string;
      job_id: string;
      pipeline_name: string;
      domain: string;
      cadence: string;
      approval_gate: string;
      activation_allowed: boolean;
      scheduler_activation: string;
      manual_next_step: string;
      generated_at: string;
      source: string;
    };
    profile_scheduler?: {
      status: string;
      install_status: string;
      scheduler_type: string;
      timer_count: number;
      active_timer_count: number;
      generated_at: string;
      source: string;
      timers: Array<{
        profile_id: string;
        service_name: string;
        timer_name: string;
        schedule: string;
        active_state: string;
        next_elapse: string;
        last_result: string;
      }>;
    };
  };
  freshness: Array<{
    dataset: string;
    status: string;
    latest_observation_date: string;
  }>;
  provider_budget: {
    provider: string;
    status: string;
    budget_date: string;
    daily_budget: number;
    used_request_count: number;
    remaining_request_count: number;
    latest_run: {
      started_at: string;
      status: string;
      requested_symbol_count: number;
      provider_request_count: number;
      budget_remaining_after: number;
    } | null;
    source: string;
  };
  manual_local_ingest_smoke: {
    status: string;
    execute: boolean;
    generated_at: string;
    runtime_status: string;
    artifact_root: string;
    job_count: number;
    planned_job_ids: string[];
    artifact_runs: Array<{
      job_id: string;
      pipeline_name: string;
      status: string;
      exit_code: number;
      artifact_dir: string;
      metadata_path: string;
      stdout_path: string;
      stderr_path: string;
      stdout_json_path: string;
    }>;
    failed_job_count: number;
    next_actions: string[];
    source: string;
  };
  local_ingest_worker: {
    status: string;
    execute: boolean;
    generated_at: string;
    completed_cycle_count: number;
    failed_cycle_count: number;
    max_cycles: number;
    interval_seconds: number;
    stop_on_failure: boolean;
    job_ids: string[];
    latest_smoke_output_path: string;
    cycles: Array<{
      cycle_number: number;
      started_at: string;
      smoke_status: string;
      runtime_status: string;
      execute: boolean;
      job_count: number;
      failed_job_count: number;
      artifact_run_count: number;
    }>;
    next_actions: string[];
    source: string;
  };
  cycle_ai_quality_audit: {
    status: string;
    execute: boolean;
    generated_at: string;
    as_of_date: string;
    lookback_days: number;
    audit_score: number;
    issue_count: number;
    readiness_gap_count: number;
    metrics: Record<string, number | string | boolean | null>;
    checks: Record<string, number | string | boolean | null>;
    samples: Record<string, unknown>;
    next_actions: string[];
    source: string;
  };
  benchmark_drift_quality: {
    status: string;
    guardrail_status: string;
    guardrail_eval_run_id: string;
    guardrail_as_of_date: string;
    drift_status: string;
    drift_calculated: boolean;
    benchmark_code: string;
    benchmark_source: string;
    source_type: string;
    source_as_of_date: string;
    source_age_days: number | null;
    component_count: number;
    composition_coverage_weight: number;
    active_share: number | null;
    total_absolute_drift: number | null;
    top_active_positions: Array<{
      symbol: string;
      portfolio_weight: number;
      benchmark_weight: number;
      active_weight: number;
    }>;
    outlier_positions: Array<{
      symbol: string;
      portfolio_weight: number;
      benchmark_weight: number;
      active_weight: number;
    }>;
    checks: Array<{
      check_key: string;
      status: string;
      detail: string;
    }>;
    next_actions: string[];
  };
  open_gates: string[];
};

export type StockPrice = {
  trade_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  adjusted_close: number | null;
  volume: number;
  change_pct?: number | null;
};

export type IndustryCompetitivePosition = {
  position_id: string;
  as_of_date: string;
  methodology: string;
  competitive_position: string;
  peer_group_id: string;
  peer_group_code: string | null;
  peer_group_name: string | null;
  sector_code: string | null;
  sector_name: string | null;
  moat_score: number | null;
  pricing_power_score: number | null;
  profitability_score: number | null;
  growth_position_score: number | null;
  financial_strength_score: number | null;
  rivalry_risk_score: number | null;
  buyer_power_risk_score: number | null;
  supplier_power_risk_score: number | null;
  substitute_threat_risk_score: number | null;
  new_entry_threat_risk_score: number | null;
  capacity_cycle_risk_score: number | null;
  metric_coverage_count: number;
  peer_count: number;
  key_strengths: string[];
  key_risks: string[];
  peer_context: Record<string, unknown>;
  rationale: string | null;
  source_run_id: string | null;
};

export type StockRecommendation = {
  recommendation_id: string;
  linked_thesis_id: string | null;
  action: string;
  score: number | null;
  status: string;
  as_of_date: string;
};

export type StockPosition = {
  portfolio_name: string;
  snapshot_date: string;
  quantity: number | null;
  weight: number | null;
  market_price: number | null;
  market_value: number | null;
  linked_thesis_id: string | null;
};

export type StockListData = {
  as_of_date: string;
  stock_count: number;
  summary: {
    latest_price_date: string;
    priced_stock_count: number;
    recommended_stock_count: number;
    held_stock_count: number;
  };
  stocks: Array<{
    symbol: string;
    name: string;
    instrument_id: string;
    market_code: string;
    currency_code: string;
    latest_price: StockPrice;
    data_coverage: {
      bar_count: number;
      first_trade_date: string;
      last_trade_date: string;
    };
    recommendation: StockRecommendation | null;
    position: StockPosition | null;
  }>;
};

export type StockDetailData = {
  symbol: string;
  name: string;
  instrument_id: string;
  market_code: string;
  currency_code: string;
  as_of_date: string;
  latest_price: StockPrice;
  summary: {
    bar_count: number;
    first_trade_date: string;
    last_trade_date: string;
    low_close: number | null;
    high_close: number | null;
    return_pct: number | null;
  };
  price_bars: StockPrice[];
  recommendation: StockRecommendation | null;
  position: StockPosition | null;
  equity_research: {
    artifact_id: string;
    as_of_date: string;
    artifact_type: string;
    provider: string;
    model_name: string;
    title: string;
    korean_summary: string;
    key_points: string[];
    catalysts: string[];
    risks: string[];
    invalidation_conditions: string[];
    valuation_sensitivity: Record<string, unknown>;
    source_document_ids: string[];
    source_run_id: string | null;
    created_at: string;
  } | null;
  industry_competitive_position: IndustryCompetitivePosition | null;
  macro_flow_impacts: Array<{
    event_id: string;
    title: string;
    korean_title?: string | null;
    korean_summary?: string | null;
    translation_confidence?: number | null;
    event_type: string;
    event_at: string;
    theme_key: string;
    theme_name: string;
    impact_direction: string;
    impact_score: number | null;
    confidence: number | null;
    exposure_weight: number | null;
    rationale: string;
    source_document_id: string | null;
    ai_evidence_id: string | null;
    source_run_id: string | null;
  }>;
  recent_events: Array<{
    event_id: string;
    title: string;
    korean_title?: string | null;
    korean_summary?: string | null;
    translation_confidence?: number | null;
    event_type: string;
    event_at: string;
    impact_direction: string;
    impact_score: number | null;
    source_document_id: string | null;
    ai_evidence_id: string | null;
  }>;
};

export type AiEvidenceNeighborhoodData = {
  symbol: string;
  as_of_date: string;
  retrieval_boundary: {
    mode: string;
    retrieval_backend: string;
    vector_backend: string;
    graph_backend: string;
    live_llm_call_enabled: boolean;
    token_budget: number;
    cost_estimate_usd: number;
  };
  instrument: {
    symbol: string;
    instrument_id: string;
    name: string;
    market_code: string;
    found: boolean;
  };
  summary: {
    theme_count: number;
    theme_edge_count: number;
    event_count: number;
    story_group_count: number;
    ai_artifact_count: number;
    evidence_chunk_count: number;
    embedded_chunk_count: number;
    thesis_count: number;
    recommendation_count: number;
    position_count: number;
  };
  themes: Array<{
    theme_key: string;
    theme_name: string;
    taxonomy_family: string;
    node_type: string;
    membership_type: string;
    confidence: number | null;
    source_document_id: string | null;
  }>;
  theme_edges: Array<{
    edge_id: string;
    parent_theme_key: string;
    child_theme_key: string;
    relation_type: string;
    weight: number | null;
  }>;
  events: Array<{
    event_id: string;
    title: string;
    korean_title?: string | null;
    korean_summary?: string | null;
    translation_confidence?: number | null;
    event_type: string;
    event_at: string;
    theme_key: string;
    impact_direction: string;
    impact_score: number | null;
    source_document_id: string | null;
  }>;
  story_groups: Array<{
    story_id: string;
    story_key: string;
    title: string;
    korean_title?: string | null;
    korean_summary?: string | null;
    translation_confidence?: number | null;
    confidence: number;
    event_count: number;
    source_document_count: number;
    linked_chunk_count: number;
    latest_event_at: string;
    theme_keys: string[];
    source_document_ids: string[];
    linked_chunk_ids: string[];
    basis: string[];
    relation_reasons: string[];
    events: Array<{
      event_id: string;
      title: string;
      korean_title?: string | null;
      korean_summary?: string | null;
      translation_confidence?: number | null;
      event_type: string;
      event_at: string;
      theme_key: string;
      impact_direction: string;
      impact_score: number | null;
      source_document_id: string | null;
    }>;
  }>;
  ai_artifacts: Array<{
    evidence_id: string;
    evidence_type: string;
    event_id: string | null;
    source_document_id: string | null;
    provider: string;
    model_id: string;
    status: string;
    confidence: number | null;
    estimated_cost_usd: number | null;
  }>;
  evidence_chunks: Array<{
    chunk_id: string;
    source_document_id: string;
    chunk_index: number;
    text_preview: string;
    token_count: number;
    source_url_host: string;
    source_text_kind: string;
    used_metadata_fallback: boolean;
    embedding_status: string;
    embedding_provider: string;
    embedding_model_id: string;
  }>;
  theses: Array<{
    thesis_id: string;
    title: string;
    status: string;
    conviction_score: number | null;
    expected_holding_days: number;
    invalidation_conditions: string;
  }>;
  recommendations: Array<{
    recommendation_id: string;
    as_of_date: string;
    action: string;
    bucket: string;
    total_score: number | null;
    recommended_weight: number | null;
    linked_thesis_id: string | null;
  }>;
  positions: Array<{
    portfolio_name: string;
    snapshot_date: string;
    market_value: number | null;
    weight: number | null;
    linked_thesis_id: string | null;
  }>;
  guardrails: string[];
};

export type AiNewsClusterListData = {
  as_of_date: string;
  filters: {
    theme_key: string | null;
    symbol: string | null;
  };
  summary: {
    cluster_count: number;
    clustered_event_count: number;
    source_document_count: number;
    chunk_count: number;
    embedded_chunk_count: number;
    local_rule_cluster_count: number;
    llm_candidate_invocation_count: number;
    llm_candidate_success_count: number;
    llm_candidate_failed_count: number;
    llm_candidate_artifact_count: number;
    latest_llm_invocation_status: string;
    latest_llm_invocation_at: string;
    latest_llm_success_at: string;
    latest_llm_failure_at: string;
    latest_llm_provider: string;
    estimated_cost_usd: number;
  };
  clusters: Array<{
    evidence_id: string;
    title: string;
    evidence_type: string;
    created_at: string;
    confidence: number | null;
    theme_key: string;
    theme_name: string;
    story_key: string;
    story_label: string;
    as_of_date: string;
    event_count: number;
    symbols: string[];
    direction_counts: Record<string, number>;
    representative_event_id: string | null;
    request_hash: string;
    source_document_count: number;
    chunk_count: number;
    embedded_chunk_count: number;
    representative_source_document_id: string | null;
    extraction_run: {
      run_id: string;
      status: string;
      provider: string;
      model_id: string;
      reasoning_effort: string;
      input_tokens: number;
      output_tokens: number;
      estimated_cost_usd: number;
      request_hash: string;
    };
    events: Array<{
      event_id: string;
      title: string;
      korean_title?: string | null;
      korean_summary?: string | null;
      translation_confidence?: number | null;
      event_at: string;
      symbol: string;
      impact_direction: string;
      impact_score: number | null;
      source_document_id: string;
    }>;
    source_documents: Array<{
      source_document_id: string;
      title: string;
      korean_title?: string | null;
      korean_summary?: string | null;
      translation_confidence?: number | null;
      url: string;
      published_at: string;
      chunk_count: number;
      embedded_chunk_count: number;
    }>;
    relation_reasons: string[];
    audit_notes: string[];
  }>;
  guardrails: string[];
};

export type PaperTradingPreviewData = {
  as_of_date: string;
  portfolio_name: string;
  strategy_name: string;
  latest_recommendation_batch: {
    as_of_date: string;
    horizon_type: string;
    universe_version: string;
  };
  quality_summary: {
    recommendation_count: number;
    measured_recommendation_count: number;
    unmeasured_recommendation_count: number;
    hit_rate: number | null;
    average_alpha: number | null;
    position_recommendation_conflict_count: number;
    paper_action_count: number;
    requires_human_approval_count: number;
  };
  guardrails: string[];
  paper_actions: Array<{
    symbol: string;
    instrument_id: string;
    recommendation_id: string | null;
    linked_thesis_id: string | null;
    recommendation_action: string;
    recommendation_score: number | null;
    recommendation_as_of_date: string;
    latest_price_date: string;
    latest_price: number | null;
    current_weight: number | null;
    target_weight: number | null;
    paper_action: string;
    reason: string;
    risk_level: RiskLevel;
    requires_human_approval: boolean;
    conflict: boolean;
  }>;
};

export type TradingGateStatus = "pass" | "warning" | "missing" | "blocked";

export type TradingReadinessData = {
  portfolio_name: string;
  execution_mode: string;
  readiness_status: string;
  gate_summary: {
    pass_count: number;
    warning_count: number;
    missing_count: number;
    blocked_count: number;
  };
  gates: Array<{
    gate_key: string;
    label: string;
    status: TradingGateStatus;
    detail: string;
    next_step: string;
  }>;
  broker_boundary: {
    broker_code: string;
    environment: string;
    status: string;
    supports_order_preview: boolean;
    supports_order_submit: boolean;
    secret_configured: boolean;
    notes: string;
    updated_at: string;
  };
  account_permission: {
    account_ref: string;
    permission_scope: string;
    status: string;
    allowed_symbol_count: number;
    allows_all_symbols: boolean;
    max_order_notional: number | null;
    max_daily_notional: number | null;
    approved_by: string;
    approved_at: string;
    updated_at: string;
  };
  order_limit_policy: {
    policy_name: string;
    status: string;
    max_single_order_notional: number | null;
    max_daily_order_notional: number | null;
    max_single_order_weight_delta: number | null;
    max_post_trade_symbol_weight: number | null;
    min_cash_buffer_weight: number | null;
    updated_at: string;
  };
  kill_switches: Array<{
    scope: string;
    scope_ref: string;
    is_engaged: boolean;
    reason: string;
    changed_by: string;
    changed_at: string;
  }>;
  paper_validation: {
    validation_date: string;
    status: string;
    recommendation_count: number;
    conflict_count: number;
    approved_action_count: number;
    validated_symbol_count: number;
    blocked_reasons: string[];
    created_by: string;
    created_at: string;
  };
  portfolio_risk_budget_guardrail: {
    status: string;
    eval_run_id: string | null;
    as_of_date: string;
    effective_snapshot_date: string;
    risk_gate_decision: string;
    paper_validation_input_allowed: boolean;
    blocking_reasons: string[];
    warning_reasons: string[];
    benchmark_drift?: Record<string, unknown>;
  };
  audit_summary: {
    intent_count: number;
    blocked_count: number;
    approved_for_paper_count: number;
    approved_for_live_count: number;
    submitted_to_broker_count: number;
    latest_created_at: string;
  };
  guardrails: string[];
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

export type CycleMapData = {
  as_of_date: string;
  summary: {
    node_count: number;
    macro_count: number;
    domain_count: number;
    sector_count: number;
    theme_count: number;
    instrument_count: number;
    conflict_node_count: number;
    direct_event_count: number;
    propagated_impact_count: number;
    recommendation_count: number;
    thesis_count: number;
    hot_node_code: string | null;
  };
  nodes: Array<{
    node_id: string;
    node_code: string;
    node_name: string;
    node_type: string;
    description: string | null;
    cycle_level: string;
    cycle_state: string;
    cycle_score: number | null;
    trend_score: number | null;
    breadth_score: number | null;
    event_heat_score: number | null;
    liquidity_score: number | null;
    valuation_pressure: number | null;
    parent_alignment_score: number | null;
    conflict_flags: string[];
    evidence_event_ids: string[];
    summary_text_ko: string;
    top_symbols: string[];
    recent_event_titles: string[];
    parent_codes: string[];
    child_codes: string[];
    counts: {
      parent_edge_count: number;
      child_edge_count: number;
      direct_event_count: number;
      propagated_impact_count: number;
      exposed_instrument_count: number;
      ai_artifact_count: number;
      recommendation_count: number;
      thesis_count: number;
    };
    summary_as_of_date: string | null;
    source_run_id: string | null;
    updated_at: string;
  }>;
  edges: Array<{
    parent_code: string;
    parent_name: string;
    child_code: string;
    child_name: string;
    relation_type: string;
    weight: number | null;
  }>;
};

export type RecommendationListData = {
  as_of_date: string;
  strategy_name: string;
  horizon_type: string;
  universe_version: string;
  recommendation_count: number;
  summary: {
    active_count: number;
    reviewable_count: number;
    blocked_count: number;
    measured_count: number;
    linked_thesis_count: number;
    ai_or_event_evidence_count: number;
    macro_flow_evidence_recommendation_count: number;
    average_score: number | null;
  };
  recommendations: Array<{
    recommendation_id: string;
    symbol: string;
    name: string;
    instrument_id: string;
    as_of_date: string;
    rank_position: number;
    bucket: string;
    action: string;
    status: string;
    score: number;
    recommended_weight: number | null;
    linked_thesis_id: string | null;
    evidence: {
      score_component_count: number;
      ai_or_event_component_count: number;
      market_or_rank_component_count: number;
      macro_flow_component_count: number;
      macro_flow_evidence_count: number;
      quality_status: string;
      primary_evidence_id: string | null;
    };
    outcome: {
      measurement_end_date: string;
      label: string;
      alpha: number | null;
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
    provenance?: {
      source_type: string;
      label: string;
      component: string;
      feature_code: string | null;
      feature_name: string | null;
      description: string | null;
      feature_value: number | null;
      zscore: number | null;
      as_of_date: string | null;
      source_run_id: string | null;
      universe_batch_id: string | null;
      rank_position: number | null;
      universe_member_count: number | null;
      selection_score: number | null;
      selection_rule: string | null;
      latest_trade_date: string | null;
      observation_count: number | null;
      inclusion_reason: string | null;
      evidence: {
        feature_set_version: string | null;
        universe_batch_id: string | null;
        rank_position: number | null;
        observation_count: number | null;
        first_trade_date: string | null;
        latest_trade_date: string | null;
        as_of_date: string | null;
        cycle_stack_node_code?: string | null;
        cycle_stack_level?: string | null;
        cycle_stack_explanation?: string | null;
        cycle_stack_note?: string | null;
        fundamental_component_name?: string | null;
        fundamental_explanation?: string | null;
        fundamental_note?: string | null;
        propagated_impact_count?: number | null;
        recent_flows?: Array<{
          event_id: number | string;
          title: string;
          korean_title?: string | null;
          korean_summary?: string | null;
          translation_confidence?: number | null;
          event_at: string;
          theme_key: string;
          theme_name: string;
          impact_direction: string;
          impact_strength: number | null;
          confidence: number | null;
          exposure_weight: number | null;
        }>;
      };
    };
  }>;
  equity_research: {
    artifact_id: string;
    as_of_date: string;
    artifact_type: string;
    provider: string;
    model_name: string;
    title: string;
    korean_summary: string;
    key_points: string[];
    catalysts: string[];
    risks: string[];
    invalidation_conditions: string[];
    valuation_sensitivity: Record<string, unknown>;
    source_document_ids: string[];
    source_run_id: string | null;
    created_at: string;
  } | null;
  industry_competitive_position: IndustryCompetitivePosition | null;
  linked_thesis_id: string;
  evidence_trace: {
    symbol: string;
    as_of_date: string;
    direct_news_or_ai: {
      status: string;
      evidence_id: string | null;
      event_id: string | null;
      ai_evidence_id: string | null;
      title: string | null;
      korean_title?: string | null;
      korean_summary?: string | null;
      translation_confidence?: number | null;
      event_at: string;
      impact_direction: string;
      impact_strength: number | null;
      confidence: number | null;
      rationale: string | null;
    };
    macro_flow: {
      status: string;
      propagated_impact_count: number;
      source_run_id: string | null;
      recent_flows: Array<{
        event_id: string;
        title: string;
        korean_title?: string | null;
        korean_summary?: string | null;
        translation_confidence?: number | null;
        event_at: string;
        theme_key: string;
        theme_name: string;
        impact_direction: string;
        impact_strength: number | null;
        confidence: number | null;
        exposure_weight: number | null;
      }>;
    };
    holding_review: {
      status: string;
      portfolio_name: string;
      portfolio_review_id: string | null;
      review_item_id: string | null;
      review_date: string | null;
      review_source: string | null;
      risk_level: string | null;
      source_run_id: string | null;
      action: string;
      reason: string | null;
      priority: number | null;
      health_score: number | null;
      current_weight: number | null;
      recommended_weight: number | null;
      weight_gap: number | null;
      market_value: number | null;
      position_snapshot_date: string | null;
      position_source_run_id: string | null;
      position_linked_thesis_id: string | null;
    };
  };
  evidence_review: EvidenceReviewData;
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
    summary: string;
    change_notes: string;
    next_review_date: string;
  };
  lifecycle: {
    source: string;
    equity_research_artifact_id: string | null;
    buy_case: {
      symbol: string;
      summary: string;
      core_claims: string[];
    };
    catalysts: string[];
    risks: string[];
    invalidation_conditions: Array<{
      condition: string;
      current_status: string;
    }>;
    valuation: {
      base_case: string | null;
      upside_case: string | null;
      downside_case: string | null;
      margin_of_safety_view: string | null;
      confidence: number | null;
      raw: Record<string, unknown>;
      has_view: boolean;
    };
    review_cadence: {
      latest_review_action: string;
      risk_level: RiskLevel;
      reviewed_at: string;
      next_review_date: string;
      summary: string;
    };
    readiness: {
      status: string;
      missing_items: string[];
      core_claim_count: number;
      catalyst_count: number;
      risk_count: number;
      invalidation_count: number;
      has_valuation_view: boolean;
      has_next_review_date: boolean;
    };
  };
  evidence: Array<{
    evidence_id: string;
    type: string;
    title: string;
  }>;
  evidence_review: EvidenceReviewData;
};

export type EvidenceReviewData = {
  quality_status: string;
  summary: Record<string, number | boolean>;
  gates: Array<{
    gate_key: string;
    label: string;
    status: "pass" | "warning" | "blocked" | string;
    detail: string;
    next_step: string;
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
  allocation_policy: {
    policy_id: string;
    policy_name: string;
    status: string;
    policy_scope: string;
    max_single_position_weight: number | null;
    min_rebalance_target_weight: number | null;
    valid_from: string;
    valid_to: string;
    rationale: string;
  };
  risk_budget: {
    status: string;
    max_single_position_weight: number | null;
    min_rebalance_target_weight: number | null;
    max_sector_weight: number | null;
    max_theme_weight: number | null;
    max_unclassified_weight: number | null;
    largest_position_symbol: string | null;
    largest_position_weight: number | null;
    over_single_position_limit_count: number;
    below_rebalance_floor_count: number;
    cash_weight: number | null;
    invested_weight: number | null;
    concentration: {
      status: string;
      max_sector_weight: number | null;
      max_theme_weight: number | null;
      max_unclassified_weight: number | null;
      sector_exposures: Array<{
        exposure_type: string;
        exposure_key: string;
        exposure_name: string;
        exposure_weight: number;
        position_count: number;
        symbols: string[];
        limit: number;
        excess_weight: number;
        status: string;
      }>;
      theme_exposures: Array<{
        exposure_type: string;
        exposure_key: string;
        exposure_name: string;
        exposure_weight: number;
        position_count: number;
        symbols: string[];
        limit: number;
        excess_weight: number;
        status: string;
      }>;
      unclassified_weight: number;
      unclassified_symbols: string[];
      over_limit_count: number;
      review_reasons: string[];
    };
    rebalance_priorities: Array<{
      symbol: string;
      current_weight: number | null;
      priority: number;
      action: string;
      reason: string;
      order_boundary: string;
    }>;
    review_reasons: string[];
  };
  positions: Array<{
    symbol: string;
    instrument_id: string;
    weight: number;
    coverage_status: string;
    active_thesis_id: string | null;
    outcome_status: string;
    action: string;
    position_size_status: string;
    max_single_position_weight: number | null;
    min_rebalance_target_weight: number | null;
    weight_to_single_position_limit: number | null;
    position_size_note: string;
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
  korean_title?: string | null;
  korean_summary?: string | null;
  translation_confidence?: number | null;
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
    estimated_cost_usd: number | null;
    quality_gate: string;
  };
  extracted_fields: Array<{
    field: string;
    value: string;
    confidence: number;
    source_chunk_id: string;
  }>;
  news_candidate: {
    analysis_method: string;
    event_summary: string;
    recommendation_relevance: string;
    uncertainty_notes: string;
    theme_impacts: Array<{
      target: string;
      impact_direction: string;
      impact_strength: number | null;
      confidence: number | null;
      rationale: string;
      evidence_summary: string;
    }>;
    instrument_impacts: Array<{
      target: string;
      impact_direction: string;
      impact_strength: number | null;
      confidence: number | null;
      rationale: string;
      evidence_summary: string;
    }>;
  } | null;
  retrieval_context_summary: {
    as_of_date: string;
    known_themes: Array<Record<string, unknown>>;
    theme_edges: Array<Record<string, unknown>>;
    current_event_impacts: Array<Record<string, unknown>>;
    recent_similar_events: Array<Record<string, unknown>>;
  };
  cluster_summary: {
    as_of_date: string;
    theme_key: string;
    theme_name: string;
    story_key: string;
    story_label: string;
    event_count: number;
    symbols: string[];
    direction_counts: Record<string, number>;
    representative_event_id: string | null;
    request_hash: string;
  } | null;
  cluster_events: Array<{
    event_id: string;
    title: string;
    korean_title?: string | null;
    korean_summary?: string | null;
    translation_confidence?: number | null;
    event_at: string;
    symbol: string;
    impact_direction: string;
    impact_score: number | null;
    source_document_id: string;
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
  korean_title?: string | null;
  korean_summary?: string | null;
  translation_confidence?: number | null;
  translation_provider?: string | null;
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
    evidence_type: string;
  };
  summary: {
    event_count: number;
    ai_extracted_count: number;
    news_event_candidate_count: number;
    news_cluster_summary_count: number;
    suppressed_low_signal_candidate_count: number;
    unreviewed_event_count: number;
    source_document_count: number;
    themes_represented: number;
  };
  events: Array<{
    event_id: string;
    title: string;
    korean_title?: string | null;
    korean_summary?: string | null;
    translation_confidence?: number | null;
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
    ai_evidence_type: string | null;
    ai_evidence_provider: string | null;
    ai_evidence_confidence: number | null;
    quality_gate: string;
    related_events: Array<{
      event_id: string;
      title: string;
      korean_title?: string | null;
      korean_summary?: string | null;
      translation_confidence?: number | null;
      relation_type: string;
      relation_strength: number;
      reason: string;
      symbol: string;
      theme_key: string;
      event_at: string;
    }>;
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

export type PerformanceOutcomesData = {
  portfolio_name: string;
  strategy_name: string;
  snapshot_date: string;
  measurement_start_date: string;
  measurement_end_date: string;
  benchmark_code: string;
  methodology: string;
  summary: {
    measured_recommendation_count: number;
    measured_thesis_count: number;
    outperform_count: number;
    underperform_count: number;
    hit_rate: number;
    average_alpha: number;
    security_lens_contribution_bps: number;
    theme_lens_contribution_bps: number;
    cash_timing_contribution_bps: number;
    attribution_component_count: number;
    excluded_position_count: number;
    excluded_weight: number;
    cash_weight: number;
  };
  quality_evaluation: {
    status: string;
    sample_size_status: string;
    score_outcome_alignment: string;
    review_outcome_mismatch_count: number;
    measured_recommendation_count: number;
    measured_thesis_count: number;
    average_alpha: number | null;
    hit_rate: number | null;
    high_score_recommendation_count: number;
    high_score_average_alpha: number | null;
    coverage_exclusion_count: number;
    checks: Array<{
      check_key: string;
      label: string;
      status: string;
      detail: string;
      next_step: string;
    }>;
  };
  outcomes: Array<{
    outcome_id: string;
    recommendation_id: string;
    thesis_id: string;
    symbol: string;
    instrument_id: string;
    recommendation: string;
    horizon_days: number;
    absolute_return: number;
    benchmark_return: number;
    alpha: number;
    label: string;
    position_weight: number;
    security_contribution_bps: number;
    source_run_id: string;
  }>;
  attribution_components: Array<{
    component_id: string;
    component_type: string;
    label: string;
    symbol: string;
    theme_key: string | null;
    weight: number;
    absolute_return: number;
    benchmark_return: number;
    alpha: number;
    contribution_bps: number;
    interpretation: string;
  }>;
  coverage_exclusions: Array<{
    symbol: string;
    instrument_id: string;
    weight: number;
    reason: string;
    required_action: string;
  }>;
  quality_gates: Array<{
    gate: string;
    status: string;
    reason: string;
  }>;
};
