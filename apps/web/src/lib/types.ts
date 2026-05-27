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
  production_api_server: {
    status: string;
    attention_required: boolean;
    service: string;
    runtime_profile: string;
    source_mode: string;
    auth_mode: string;
    read_auth_required: boolean;
    read_token_configured: boolean;
    allowed_origin_configured: boolean;
    database_configured: boolean;
    connection_boundary: string;
    request_timeout_seconds: number;
    read_only: boolean;
    missing_conditions: string[];
    order_boundary: string;
    automatic_action_allowed: boolean;
    next_action: string;
  };
  auth_rbac: {
    status: string;
    attention_required: boolean;
    mode: string;
    auth_mode: string;
    read_role: string;
    read_allowed_roles: string[];
    read_token_configured: boolean;
    role_valid: boolean;
    protected_paths: string[];
    public_paths: string[];
    allowed_methods: string[];
    write_methods_allowed: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
    missing_conditions: string[];
    summary: string;
    next_action: string;
  };
  alert_destination: {
    status: string;
    attention_required: boolean;
    mode: string;
    destination_type: string;
    external_destination: boolean;
    local_only: boolean;
    target_configured: boolean;
    status_artifact_configured: boolean;
    status_artifact_loaded: boolean;
    last_test_status: string;
    last_tested_at: string;
    test_recent: boolean;
    test_age_hours: number | null;
    max_test_age_hours: number;
    missing_conditions: string[];
    summary: string;
    next_action: string;
    order_boundary: string;
    automatic_action_allowed: boolean;
  };
  freshness: Array<{
    dataset: string;
    status: string;
    latest_observation_date: string;
  }>;
  data_operations_artifact_runner: {
    status: string;
    attention_required: boolean;
    job_count: number;
    artifact_policy_count: number;
    latest_run_count: number;
    failed_or_missing_count: number;
    degraded_count: number;
    profile_scheduler_installed: boolean;
    timer_count: number;
    active_timer_count: number;
    manual_smoke_status: string;
    local_worker_status: string;
    latest_artifact_root: string;
    order_boundary: string;
    automatic_action_allowed: boolean;
    next_action: string;
  };
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
  news_ai_eval_quality: {
    status: string;
    eval_run_id: string;
    created_at: string;
    eval_name: string;
    dataset_version: string;
    provider: string;
    model_name: string;
    overall_pass: boolean;
    case_count: number;
    passed_case_count: number;
    failed_case_count: number;
    theme_precision: number;
    direct_ticker_grounding_precision: number;
    macro_only_false_ticker_rate: number;
    macro_only_false_ticker_count: number;
    quantum_energy_misclassification_count: number;
    blocked_candidate_correctness: number;
    korean_translation_availability: number;
    metrics: Record<string, number | string | boolean | null>;
    pass_thresholds: Record<string, number | string | boolean | null>;
    case_results: Array<{
      case_id: string;
      category: string;
      passed: boolean;
      accepted_theme_codes: string[];
      accepted_direct_symbols: string[];
      missing_theme_codes: string[];
      missing_direct_symbols: string[];
      forbidden_theme_hits: string[];
      forbidden_symbol_hits: string[];
      blocked_symbols_accepted: string[];
      rejected_impact_count: number;
      translation_available: boolean;
    }>;
    next_action: string;
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
    outlier_decisions: BenchmarkRebalanceCandidate[];
    review_candidate_count: number;
    review_decision_counts: Record<string, number>;
    attention_required: boolean;
    managed_review_status: string;
    managed_review_reason: string;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
    checks: Array<{
      check_key: string;
      status: string;
      detail: string;
    }>;
    next_actions: string[];
  };
  portfolio_review_decision_history: PortfolioReviewDecisionHistory;
  portfolio_review_decision_feedback: PortfolioReviewDecisionFeedback;
  portfolio_review_feedback_calibration: PortfolioReviewFeedbackCalibration;
  portfolio_review_feedback_cadence: PortfolioReviewFeedbackCadence;
  portfolio_review_feedback_action_router: PortfolioReviewFeedbackActionRouter;
  recommendation_outcome_calibration: {
    status: string;
    eval_run_id: string;
    created_at: string;
    as_of_date: string;
    horizon_days: number[];
    quality_status: string;
    sample_status: string;
    recommendation_horizon_count: number;
    recommendation_count: number;
    outcome_count: number;
    outcome_coverage_rate: number;
    ready_for_backfill_count: number;
    missing_entry_price_count: number;
    missing_exit_price_count: number;
    missing_reason_counts: Record<string, number>;
    component_diagnostic_count: number;
    next_action: string;
    recommendation_scoring_mutated: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
  };
  recommendation_outcome_maturity: {
    status: string;
    as_of_date: string;
    source_calibration_eval_run_id: string;
    horizon_days: number[];
    recommendation_horizon_count: number;
    recommendation_count: number;
    outcome_count: number;
    not_due_count: number;
    ready_for_backfill_count: number;
    due_today_count: number;
    overdue_count: number;
    price_gap_count: number;
    missing_entry_price_count: number;
    missing_exit_price_count: number;
    next_due_date: string;
    next_due_count: number;
    examples: Array<{
      symbol: string;
      recommendation_id: string;
      recommendation_date: string;
      horizon_days: number;
      expected_measurement_end_date: string;
      status: string;
    }>;
    cadence_action: {
      status: string;
      action_type: string;
      scheduler_job_id: string;
      pipeline_name: string;
      should_run_now: boolean;
      should_wait: boolean;
      requires_price_backfill: boolean;
      wait_until: string;
      command: string;
      follow_up_command?: string;
      label: string;
      reason: string;
      blocks_weight_review: boolean;
      automatic_weight_change_allowed: boolean;
      automatic_order_allowed: boolean;
      broker_submit_allowed: boolean;
    };
    recommendation_scoring_mutated: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
  };
  recommendation_outcome_due_action_router: RecommendationOutcomeDueActionRouter;
  recommendation_weight_review_readiness: {
    status: string;
    eval_run_id: string;
    created_at: string;
    decision: string;
    manual_weight_review_allowed: boolean;
    source_quality_status: string;
    source_eval_run_id: string;
    outcome_calibration_status: string;
    outcome_calibration_eval_run_id: string;
    blocker_code: string;
    blocker_message: string;
    next_action: string;
    automatic_weight_change_allowed: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
  };
  professional_source_gap_prioritization: {
    status: string;
    as_of_date: string;
    gap_count: number;
    high_priority_count: number;
    source_blocker_count: number;
    fund_not_applicable_count: number;
    fund_source_gap_count: number;
    coverage_gap_count: number;
    guarded_source_blocked_recommendation_count: number;
    attention_required: boolean;
    top_priority_score: number;
    gaps: Array<{
      priority_rank: number;
      symbol: string;
      instrument_id: string;
      instrument_name: string;
      instrument_type: string;
      product_type: string;
      gap_status: string;
      priority_band: string;
      priority_score: number;
      active_recommendation_count: number;
      highest_recommendation_score: number | null;
      current_weight: number | null;
      max_recommended_weight: number | null;
      missing_layer_count: number;
      missing_layers: string[];
      missing_layer_labels: string[];
      blocker_type: string;
      blocker_code: string;
      blocker_label: string;
      professional_decision_use_allowed: boolean;
      active_recommendation_professional_use_blocked: boolean;
      paper_validation_input_allowed: boolean;
      source_run_id: string;
      source_status: string;
      source_observed_at: string;
      source_error_summary: string;
      remediation_action: string;
      remediation_command: string;
      detail_href: string;
    }>;
    next_action: string;
    recommendation_scoring_mutated: boolean;
    automatic_weight_change_allowed: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
  };
  open_gates: string[];
  open_gate_details?: Array<{
    gate_id: string;
    label: string;
    category: string;
    category_label: string;
    severity: "low" | "medium" | "high" | string;
    status_label: string;
    summary: string;
    next_action: string;
    order_boundary: string;
    automatic_action_allowed: boolean;
  }>;
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

export type ValuationMethodSnapshot = {
  valuation_snapshot_id: string | null;
  method: string;
  method_label: string;
  as_of_date: string;
  base_price: number | null;
  fair_value_low: number | null;
  fair_value_base: number | null;
  fair_value_high: number | null;
  margin_of_safety: number | null;
  confidence: number | null;
  assumptions: Record<string, unknown>;
  upside_low: number | null;
  upside_base: number | null;
  upside_high: number | null;
  valuation_gap: number | null;
  evidence_summary: string;
  assumption_items: Array<{
    label: string;
    value: string;
    interpretation: string;
  }>;
  sensitivity_cases: Array<{
    case_key: string;
    label: string;
    fair_value: number | null;
    upside: number | null;
    margin_of_safety: number | null;
    description: string;
  }>;
  forecast_evidence: {
    status: string;
    label: string;
    latest_forecast_as_of_date: string;
    forecast_row_count: number;
    scenario_count: number;
    source: string;
    scenarios: Array<{
      scenario_key: string;
      label: string;
      row_count: number;
      first_year: number | null;
      last_year: number | null;
      terminal_revenue: number | null;
      terminal_free_cash_flow: number | null;
      avg_revenue_growth_rate: number | null;
      avg_free_cash_flow_margin: number | null;
      avg_capex_intensity: number | null;
      confidence: number | null;
    }>;
  };
  sotp_evidence: {
    status: string;
    label: string;
    latest_sotp_as_of_date: string;
    component_count: number;
    source: string;
    components: Array<{
      component_key: string;
      component_label: string;
      component_type: string;
      fair_value_low: number | null;
      fair_value_base: number | null;
      fair_value_high: number | null;
      valuation_basis: string;
      description: string;
      confidence: number | null;
    }>;
    reported_segment_inputs: Array<{
      segment_key: string;
      segment_label: string;
      period_end: string;
      revenue: number | null;
      operating_income: number | null;
      operating_margin: number | null;
      metric_unit: string;
      source_document_id: string | null;
      confidence: number | null;
      source_run_id: string | null;
    }>;
    reported_segment_allocations: Array<{
      segment_key: string;
      segment_label: string;
      period_end: string;
      allocation_basis: string;
      allocation_weight: number | null;
      revenue_share: number | null;
      operating_income_share: number | null;
      allocated_fair_value_low: number | null;
      allocated_fair_value_base: number | null;
      allocated_fair_value_high: number | null;
      revenue: number | null;
      operating_income: number | null;
      source_document_id: string | null;
      confidence: number | null;
      source_run_id: string | null;
    }>;
    reported_segment_assumptions: Array<{
      segment_key: string;
      segment_label: string;
      period_end: string;
      driver_key: string;
      driver_label: string;
      driver_template_key: string;
      driver_template_label: string;
      calibration_method: string;
      history_period_count: number;
      first_period_end: string;
      latest_period_end: string;
      observed_revenue_cagr: number | null;
      observed_margin_change: number | null;
      base_growth_rate: number | null;
      low_growth_rate: number | null;
      high_growth_rate: number | null;
      margin_assumption: number | null;
      low_multiple: number | null;
      base_multiple: number | null;
      high_multiple: number | null;
      allocation_weight: number | null;
      allocation_basis: string;
      rationale: string;
      source_document_id: string | null;
      confidence: number | null;
      source_run_id: string | null;
    }>;
    segment_footnote_evidence: {
      status: string;
      label: string;
      latest_segment_evidence_as_of_date: string;
      evidence_count: number;
      reported_segment_metric_count: number;
      segment_data_gap_count: number;
      source: string;
      evidence_rows: Array<{
        segment_key: string;
        segment_label: string;
        evidence_type: string;
        metric_code: string;
        metric_value: number | null;
        metric_unit: string;
        period_end: string;
        source_document_id: string | null;
        evidence_text: string;
        confidence: number | null;
        source_run_id: string | null;
      }>;
    };
  };
  data_quality: {
    status: string;
    label: string;
    confidence_label: string;
    input_count: number;
    expected_input_count: number;
    data_gap_count: number;
    warning_count: number;
    warnings: string[];
  };
  limitations: string[];
  source_run_id: string | null;
  created_at: string;
};

export type ValuationTargetRange = {
  status: string;
  symbol: string;
  as_of_date: string;
  valuation_as_of_date: string;
  currency_code: string;
  method_count: number;
  base_price: number | null;
  target_low: number | null;
  target_base: number | null;
  target_high: number | null;
  upside_low: number | null;
  upside_base: number | null;
  upside_high: number | null;
  margin_of_safety: number | null;
  confidence: number | null;
  summary: string;
  methods: ValuationMethodSnapshot[];
  valuation_quality: {
    status: string;
    label: string;
    method_coverage: number;
    expected_method_count: number;
    missing_methods: string[];
    data_gap_count: number;
    warning_count: number;
    confidence: number | null;
    confidence_label: string;
    order_boundary: string;
  };
  score_policy: string;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type FinancialMetricSnapshot = {
  metric_code: string;
  label: string;
  section_key: string;
  description: string;
  polarity: string;
  metric_value: number | null;
  metric_unit: string;
  metric_status: string;
  statement_scope: string;
  fiscal_year: number | null;
  fiscal_quarter: number | null;
  period_end: string;
  as_of_date: string;
  rationale: string;
  source_run_id: string | null;
  created_at?: string;
  history?: FinancialMetricSnapshot[];
};

export type FinancialStatementModel = {
  status: string;
  symbol: string;
  as_of_date: string;
  statement_scope: string;
  latest_period_end: string;
  latest_as_of_date: string;
  latest_fiscal_year: number | null;
  latest_fiscal_quarter: number | null;
  period_count: number;
  metric_count: number;
  computed_metric_count: number;
  unavailable_metric_count: number;
  insufficient_history_metric_count: number;
  data_gap_count: number;
  status_counts: Array<{
    metric_status: string;
    metric_count: number;
  }>;
  source_data_blocker: {
    blocker_code: string;
    label: string;
    source_pipeline: string;
    source_run_id: string | null;
    status: string;
    observed_at: string;
    error_summary: string;
    summary: string;
  } | null;
  source_run_ids: string[];
  summary: string;
  sections: Array<{
    section_key: string;
    title: string;
    description: string;
    status: string;
    computed_metric_count: number;
    data_gap_count: number;
    metrics: FinancialMetricSnapshot[];
  }>;
  metrics: FinancialMetricSnapshot[];
  share_count: {
    latest_period_end: string;
    latest_fiscal_year: number | null;
    latest_shares_outstanding: number | null;
    previous_period_end: string;
    previous_shares_outstanding: number | null;
    share_count_change_pct: number | null;
    source_run_id: string | null;
  };
  score_policy: string;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type ProfessionalSourceGuardrail = {
  status: string;
  blocked: boolean;
  professional_decision_use_allowed: boolean;
  paper_validation_input_allowed: boolean;
  blocker_code: string;
  blocker_label: string;
  source_data_blocker: FinancialStatementModel["source_data_blocker"];
  summary: string;
  next_action: string;
  score_policy: string;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type FundInstrumentAnalysis = {
  status: string;
  analysis_type: string;
  symbol: string;
  summary: string;
  benchmark_code: string;
  benchmark_source: string;
  source_type: string;
  source_as_of_date: string;
  holding_count: number;
  holdings_coverage_weight: number | null;
  average_holding_confidence: number | null;
  top_holdings: Array<{
    symbol: string;
    name: string;
    target_weight: number | null;
    confidence: number | null;
    rationale: string;
  }>;
  portfolio_role: {
    portfolio_name: string;
    current_weight: number | null;
    recommended_weight: number | null;
    role: string;
    rationale: string;
  };
  tracking_error: {
    status: string;
    value: number | null;
    metric_type: string;
    tracking_difference_value: number | null;
    source_name: string;
    source_as_of_date: string;
    source_url: string;
    measurement_window: string;
    measurement_basis: string;
    benchmark_name: string;
    fund_return: number | null;
    benchmark_return: number | null;
    summary: string;
  };
  expense_ratio: {
    status: string;
    value: number | null;
    source_name: string;
    source_as_of_date: string;
    source_url: string;
    summary: string;
  };
  liquidity: {
    status: string;
    source_name: string;
    source_as_of_date: string;
    observation_count: number;
    latest_volume: number | null;
    average_daily_volume: number | null;
    average_daily_dollar_volume: number | null;
    summary: string;
  };
  nav_premium_discount: {
    status: string;
    nav_per_share: number | null;
    nav_as_of_date: string;
    bid_ask_midpoint: number | null;
    closing_price: number | null;
    market_price_as_of_date: string;
    premium_discount_to_nav: number | null;
    premium_discount_as_of_date: string;
    source_name: string;
    source_url: string;
    summary: string;
  };
  limitations: string[];
  score_policy: string;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
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
  financial_statement_model: FinancialStatementModel;
  valuation_target_range: ValuationTargetRange;
  fund_instrument_analysis: FundInstrumentAnalysis | null;
  professional_source_guardrail: ProfessionalSourceGuardrail;
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
  internal_rag_context: {
    status: string;
    symbol: string;
    as_of_date: string;
    retrieval_policy: {
      mode: string;
      retrieval_backend: string;
      canonical_store: string;
      vector_backend: string;
      graph_backend: string;
      external_rag_service: string;
      external_vector_db: string;
      external_graph_db: string;
      live_llm_call_enabled: boolean;
      write_enabled: boolean;
      broker_submit_allowed: boolean;
      order_boundary: string;
    };
    context_inventory: {
      theme_count: number;
      theme_edge_count: number;
      event_count: number;
      story_group_count: number;
      ai_artifact_count: number;
      evidence_chunk_count: number;
      translated_event_count: number;
      thesis_count: number;
      recommendation_count: number;
      position_count: number;
      estimated_prompt_chars: number;
    };
    quality_gates: Array<{
      gate: string;
      status: string;
      message_ko: string;
    }>;
    sections: Array<{
      section_id: string;
      title_ko: string;
      item_count: number;
      items: Array<{
        item_id: string;
        title_ko: string;
        summary_ko: string;
        metadata: Record<string, unknown>;
      }>;
    }>;
    evidence_items: Array<{
      evidence_id: string;
      evidence_type: string;
      title_ko: string;
      linking_reason_ko: string;
      source_document_ids: string[];
    }>;
    prompt_context: {
      language: string;
      purpose: string;
      instruction: string;
      context_char_budget: number;
      context_text: string;
    };
    guardrails: string[];
  };
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
    rebalance_candidate_review: BenchmarkRebalanceCandidateReview;
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
  currency_code: string;
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
  financial_statement_model: FinancialStatementModel;
  valuation_target_range: ValuationTargetRange;
  fund_instrument_analysis: FundInstrumentAnalysis | null;
  linked_thesis_id: string;
  professional_source_guardrail: ProfessionalSourceGuardrail;
  professional_decision_waterfall: ProfessionalDecisionWaterfall;
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

export type ProfessionalDecisionWaterfall = {
  status: string;
  summary: string;
  symbol: string;
  as_of_date: string;
  recommendation: string;
  score: number | null;
  score_component_count: number;
  paper_validation_input_allowed: boolean;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  score_policy: string;
  steps: ProfessionalDecisionStep[];
};

export type ProfessionalDecisionStep = {
  step_key: string;
  title: string;
  status: string;
  tone: "ready" | "watch" | "blocked" | "neutral" | string;
  decision: string;
  detail: string;
  evidence_count: number;
  source: string;
  href: string | null;
  href_label: string | null;
  facts: Array<{
    label: string;
    value: string;
  }>;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type ThesisDetailData = {
  thesis_id: string;
  symbol: string;
  instrument_id: string;
  currency_code: string;
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
  professional_lifecycle_gates: ProfessionalLifecycleGates;
  valuation_target_range: ValuationTargetRange;
  evidence: Array<{
    evidence_id: string;
    type: string;
    title: string;
    observed_at: string;
  }>;
  evidence_review: EvidenceReviewData;
};

export type ProfessionalLifecycleGates = {
  status: string;
  summary: string;
  gate_count: number;
  pass_count: number;
  warning_count: number;
  blocked_count: number;
  latest_evidence_at: string | null;
  latest_reviewed_at: string | null;
  next_review_date: string | null;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  gates: ProfessionalLifecycleGate[];
};

export type ProfessionalLifecycleGate = {
  gate_key: string;
  title: string;
  status: string;
  decision: string;
  detail: string;
  next_step: string;
  facts: Array<{
    label: string;
    value: string;
  }>;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
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
    rebalance_candidate_review: BenchmarkRebalanceCandidateReview;
    position_sizing_review: PositionSizingReview;
    review_decision_history: PortfolioReviewDecisionHistory;
    review_decision_feedback: PortfolioReviewDecisionFeedback;
    review_feedback_calibration: PortfolioReviewFeedbackCalibration;
    review_feedback_cadence: PortfolioReviewFeedbackCadence;
    review_feedback_action_router: PortfolioReviewFeedbackActionRouter;
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

export type BenchmarkRebalanceCandidateReview = {
  status: string;
  candidate_count: number;
  decision_counts: Record<string, number>;
  benchmark_code: string;
  benchmark_source: string;
  source_type: string;
  source_as_of_date: string;
  active_share: number | null;
  composition_coverage_weight: number;
  review_threshold_active_weight: number;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  candidates: BenchmarkRebalanceCandidate[];
  next_actions: string[];
};

export type BenchmarkRebalanceSourceEvidence = {
  benchmark_code: string;
  benchmark_source: string;
  source_type: string;
  source_as_of_date: string;
  current_weight: number;
  benchmark_weight: number;
  active_weight: number;
  active_weight_abs: number;
  review_threshold_active_weight: number;
};

export type BenchmarkRebalanceDecisionPathStep = {
  step: string;
  label: string;
  detail: string;
};

export type BenchmarkRebalanceCandidate = {
  priority: number;
  symbol: string;
  current_weight: number;
  benchmark_weight: number;
  active_weight: number;
  direction: "overweight" | "underweight" | string;
  severity: "high" | "medium" | "watch" | string;
  suggested_review_action: string;
  review_decision: string;
  decision_label: string;
  next_review_action: string;
  professional_review_required: boolean;
  source_evidence: BenchmarkRebalanceSourceEvidence;
  related_thesis_id: string | null;
  related_recommendation_id: string | null;
  related_recommendation_action: string | null;
  related_recommended_weight: number | null;
  links: Record<string, string>;
  decision_path: BenchmarkRebalanceDecisionPathStep[];
  rationale: string;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type PortfolioReviewHistoryDecision = {
  decision_family: string;
  symbol: string;
  instrument_id: string | null;
  priority: number;
  decision_type: string;
  decision_label: string;
  next_review_action: string;
  severity: string;
  current_weight: number | null;
  benchmark_weight: number | null;
  active_weight: number | null;
  source_evidence: Record<string, unknown>;
  related_thesis_id: string | null;
  related_recommendation_id: string | null;
  related_recommendation_action: string | null;
  related_recommended_weight: number | null;
  links: Record<string, string>;
  decision_path: BenchmarkRebalanceDecisionPathStep[];
  blocking_factors: string[];
  supporting_factors: string[];
  rationale: string;
  review_required: boolean;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type PortfolioReviewDecisionHistory = {
  status: string;
  eval_run_id: string;
  created_at: string;
  eval_name: string;
  dataset_version: string;
  as_of_date: string;
  portfolio_name: string;
  source_portfolio_coverage_as_of_date: string;
  coverage_measurement_end_date: string;
  decision_status: string;
  decision_count: number;
  review_required_count: number;
  benchmark_decision_count: number;
  position_sizing_decision_count: number;
  decision_counts: Record<string, number>;
  attention_required: boolean;
  managed_review_status: string;
  managed_review_reason: string;
  top_decision: PortfolioReviewHistoryDecision | null;
  latest_decisions: PortfolioReviewHistoryDecision[];
  guardrails: {
    recommendation_scoring_mutated: boolean;
    benchmark_definition_mutated: boolean;
    portfolio_position_mutated: boolean;
    automatic_rebalance_allowed: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
  };
  next_action: string;
};

export type PortfolioReviewFeedbackItem = {
  decision_index: number;
  decision_family: string;
  symbol: string;
  decision_type: string;
  decision_label: string;
  feedback_status: string;
  feedback_reason: string;
  source_decision: {
    priority: number;
    severity: string;
    current_weight: number | null;
    benchmark_weight: number | null;
    active_weight: number | null;
    related_recommendation_id: string | null;
    related_thesis_id: string | null;
    rationale: string;
  };
  evidence: {
    recommendation_outcome: {
      outcome_id: string;
      recommendation_id: string;
      measurement_end_date: string;
      horizon_days: number;
      absolute_return_pct: number | null;
      alpha_pct: number | null;
      outcome_label: string;
    };
    thesis: {
      thesis_id: string;
      status: string;
      title: string;
      conviction_score: number | null;
    };
    thesis_outcome: {
      outcome_id: string;
      thesis_id: string;
      measurement_end_date: string;
      holding_days: number;
      absolute_return_pct: number | null;
      alpha_pct: number | null;
      success_grade: string;
      summary: string;
    };
    price_evidence: {
      baseline_trade_date: string;
      baseline_adjusted_close: number | null;
      latest_trade_date: string;
      latest_adjusted_close: number | null;
      price_return_pct: number | null;
    };
    paper_validation: {
      paper_validation_run_id: string;
      validation_date: string;
      status: string;
      conflict_count: number;
      symbol_blocked: boolean;
      symbol_validated: boolean;
    };
  };
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
};

export type PortfolioReviewDecisionFeedback = {
  status: string;
  eval_run_id: string;
  created_at: string;
  eval_name: string;
  dataset_version: string;
  as_of_date: string;
  portfolio_name: string;
  source_history_eval_run_id: string;
  source_history_as_of_date: string;
  min_horizon_days: number;
  history_age_days: number;
  feedback_status: string;
  decision_count: number;
  too_early_count: number;
  validated_count: number;
  contradicted_count: number;
  needs_more_data_count: number;
  status_counts: Record<string, number>;
  paper_validation: {
    paper_validation_run_id: string;
    validation_date: string;
    status: string;
    recommendation_count: number;
    conflict_count: number;
    approved_action_count: number;
  };
  top_feedback: PortfolioReviewFeedbackItem | null;
  latest_items: PortfolioReviewFeedbackItem[];
  guardrails: {
    recommendation_scoring_mutated: boolean;
    benchmark_definition_mutated: boolean;
    portfolio_position_mutated: boolean;
    automatic_rebalance_allowed: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
  };
  next_action: string;
};

export type PortfolioReviewFeedbackGroupSummary = {
  decision_family?: string;
  decision_type?: string;
  symbol?: string;
  decision_count: number;
  mature_decision_count: number;
  too_early_count: number;
  validated_count: number;
  contradicted_count: number;
  needs_more_data_count: number;
  contradiction_rate: number;
  status_counts: Record<string, number>;
};

export type PortfolioReviewFeedbackRunSummary = {
  eval_run_id: string;
  created_at: string;
  as_of_date: string;
  feedback_status: string;
  decision_count: number;
  too_early_count: number;
  validated_count: number;
  contradicted_count: number;
  needs_more_data_count: number;
};

export type PortfolioReviewFeedbackCalibration = {
  status: string;
  eval_run_id: string;
  created_at: string;
  eval_name: string;
  dataset_version: string;
  as_of_date: string;
  portfolio_name: string;
  lookback_days: number;
  min_feedback_runs: number;
  min_mature_decisions: number;
  max_contradiction_rate: number;
  calibration_status: string;
  maturity_status: string;
  feedback_run_count: number;
  decision_count: number;
  mature_decision_count: number;
  too_early_count: number;
  validated_count: number;
  contradicted_count: number;
  needs_more_data_count: number;
  contradiction_rate: number;
  validated_rate: number;
  feedback_run_gap: number;
  mature_decision_gap: number;
  estimated_maturity_date: string;
  days_until_maturity: number | null;
  attention_required: boolean;
  weight_review_blocked: boolean;
  weight_review_block_reason: string;
  status_counts: Record<string, number>;
  family_summaries: PortfolioReviewFeedbackGroupSummary[];
  decision_type_summaries: PortfolioReviewFeedbackGroupSummary[];
  symbol_summaries: PortfolioReviewFeedbackGroupSummary[];
  latest_feedback_runs: PortfolioReviewFeedbackRunSummary[];
  guardrails: {
    recommendation_scoring_mutated: boolean;
    benchmark_definition_mutated: boolean;
    portfolio_position_mutated: boolean;
    automatic_rebalance_allowed: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
  };
  next_action: string;
  next_calibration_action: string;
};

export type PortfolioReviewFeedbackCadence = {
  status: string;
  eval_run_id: string;
  created_at: string;
  eval_name: string;
  dataset_version: string;
  as_of_date: string;
  portfolio_name: string;
  min_horizon_days: number;
  cadence_status: string;
  action_type: string;
  should_run_now: boolean;
  should_wait: boolean;
  wait_until: string;
  command: string;
  follow_up_command: string;
  label: string;
  reason: string;
  history: {
    status: string;
    eval_run_id: string;
    created_at: string;
    as_of_date: string;
    decision_status: string;
    decision_count: number;
    review_required_count: number;
  };
  feedback: {
    status: string;
    eval_run_id: string;
    created_at: string;
    as_of_date: string;
    source_history_eval_run_id: string;
    source_history_as_of_date: string;
    feedback_status: string;
    decision_count: number;
    too_early_count: number;
    validated_count: number;
    contradicted_count: number;
    needs_more_data_count: number;
  };
  calibration: {
    status: string;
    eval_run_id: string;
    created_at: string;
    as_of_date: string;
    calibration_status: string;
    feedback_run_count: number;
    decision_count: number;
    mature_decision_count: number;
    too_early_count: number;
    validated_count: number;
    contradicted_count: number;
    needs_more_data_count: number;
    latest_feedback_run_ids: string[];
  };
  evidence: {
    history_age_days: number;
    decision_count: number;
    recommendation_link_count: number;
    recommendation_outcome_count: number;
    price_evidence_count: number;
    paper_validation: {
      paper_validation_run_id: string;
      validation_date: string;
      status: string;
      recommendation_count: number;
      conflict_count: number;
      approved_action_count: number;
    };
  };
  blocks_weight_review: boolean;
  recommendation_scoring_mutated: boolean;
  benchmark_definition_mutated: boolean;
  portfolio_position_mutated: boolean;
  automatic_weight_change_allowed: boolean;
  automatic_rebalance_allowed: boolean;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  next_action: string;
};

export type PortfolioReviewFeedbackActionRouter = {
  status: string;
  eval_run_id: string;
  created_at: string;
  eval_name: string;
  dataset_version: string;
  as_of_date: string;
  portfolio_name: string;
  source_cadence_status: string;
  source_cadence_eval_run_id: string;
  source_cadence_created_at: string;
  source_cadence_as_of_date: string;
  cadence_status: string;
  source_action_type: string;
  source_should_run_now: boolean;
  route_action: string;
  action_status: string;
  reason: string;
  history_eval_run_id: string;
  feedback_eval_run_id: string;
  calibration_eval_run_id: string;
  source_cadence: {
    as_of_date: string;
    cadence_status: string;
    action_type: string;
    should_run_now: boolean;
    should_wait: boolean;
    command: string;
    follow_up_command: string;
  };
  child_runner: {
    executed: boolean;
    report_name: string;
    status: string;
    run_id: string;
    eval_run_id: string;
    feedback_status: string;
    calibration_status: string;
  };
  recommendation_scoring_mutated: boolean;
  benchmark_definition_mutated: boolean;
  portfolio_position_mutated: boolean;
  automatic_weight_change_allowed: boolean;
  automatic_rebalance_allowed: boolean;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  next_action: string;
};

export type RecommendationOutcomeDueActionRouter = {
  status: string;
  eval_run_id: string;
  created_at: string;
  eval_name: string;
  dataset_version: string;
  as_of_date: string;
  source_calibration_status: string;
  source_calibration_eval_run_id: string;
  source_calibration_created_at: string;
  source_calibration_summary: {
    as_of_date: string;
    status: string;
    quality_status: string;
    sample_status: string;
    next_action: string;
    recommendation_scoring_mutated: boolean;
    automatic_order_allowed: boolean;
    broker_submit_allowed: boolean;
    order_boundary: string;
  };
  route_action: string;
  action_status: string;
  reason: string;
  wait_until: string;
  sample_audit_summary: {
    recommendation_horizon_count: number;
    recommendation_count: number;
    outcome_count: number;
    ready_for_backfill_count: number;
    not_due_count: number;
    missing_entry_price_count: number;
    missing_exit_price_count: number;
    price_gap_count: number;
    outcome_coverage_rate: number;
  };
  missing_reason_counts: Record<string, number>;
  missing_examples: Array<{
    symbol: string;
    recommendation_id: string;
    recommendation_date: string;
    horizon_days: number;
    expected_measurement_end_date: string;
    status: string;
    benchmark_warning: string;
  }>;
  child_runner: {
    executed: boolean;
    report_name: string;
    status: string;
    run_id: string;
    eval_run_id: string;
    calibration_status: string;
    quality_status: string;
    sample_status: string;
  };
  recommendation_scoring_mutated: boolean;
  benchmark_definition_mutated: boolean;
  portfolio_position_mutated: boolean;
  automatic_weight_change_allowed: boolean;
  automatic_rebalance_allowed: boolean;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  next_action: string;
};

export type PositionSizingReview = {
  status: string;
  policy_name: string;
  candidate_count: number;
  review_required_count: number;
  reduce_review_count: number;
  add_blocked_until_evidence_count: number;
  watch_small_position_count: number;
  hold_review_count: number;
  max_single_position_weight: number | null;
  min_rebalance_target_weight: number | null;
  cash_weight: number | null;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
  candidates: PositionSizingCandidate[];
  next_actions: string[];
};

export type PositionSizingCandidate = {
  priority: number;
  symbol: string;
  instrument_id: string;
  current_weight: number | null;
  benchmark_weight: number | null;
  active_weight: number | null;
  position_size_status: string;
  thesis_status: string;
  professional_analysis_status: string;
  review_band: string;
  severity: "high" | "medium" | "watch" | "low" | string;
  related_thesis_id: string | null;
  related_recommendation_id: string | null;
  related_recommendation_action: string | null;
  related_recommended_weight: number | null;
  links: Record<string, string>;
  policy_ceiling_weight: number | null;
  review_ceiling_weight: number | null;
  fundamental_quality_score: number | null;
  valuation_margin_score: number | null;
  peer_relative_score: number | null;
  balance_sheet_risk_penalty: number | null;
  thesis_consistency_score: number | null;
  valuation_margin_of_safety: number | null;
  valuation_method_count: number;
  valuation_as_of_date: string;
  equity_research_artifact_id: string | null;
  equity_research_as_of_date: string;
  blocking_factors: string[];
  supporting_factors: string[];
  rationale: string;
  automatic_order_allowed: boolean;
  broker_submit_allowed: boolean;
  order_boundary: string;
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
  visibility_trace: {
    summary_ko: string;
    source: {
      status: string;
      source_document_id: string;
      source_document_count: number;
      source_chunk_count: number;
      message_ko: string;
    };
    translation: {
      status: string;
      translated_event_count: number;
      translation_confidence: number | null;
      message_ko: string;
    };
    ai_structure: {
      status: string;
      provider: string;
      model_id: string;
      evidence_type: string;
      extracted_field_count: number;
      theme_impact_count: number;
      instrument_impact_count: number;
      cluster_event_count: number;
      message_ko: string;
    };
    validator: {
      status: string;
      quality_gate: string;
      blocked: boolean;
      decision_ko: string;
      reasons_ko: string[];
    };
    recommendation_linkage: {
      status: string;
      target_symbol: string;
      theme_key: string;
      message_ko: string;
    };
    steps: Array<{
      step_key: string;
      label_ko: string;
      status: string;
    }>;
    read_only_boundary: {
      live_llm_call_enabled: boolean;
      write_enabled: boolean;
      broker_submit_allowed: boolean;
      order_boundary: string;
    };
  };
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
