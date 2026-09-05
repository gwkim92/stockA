import type {
  ApiResponse,
  AiAgentRegistryData,
  AiEvidenceNeighborhoodData,
  AiEvidenceDetailData,
  AiNewsClusterListData,
  CodexOauthOperatorStatus,
  CycleStateListData,
  CycleMapData,
  DailyCockpitData,
  DataHealthData,
  EventListData,
  MarketMapData,
  PaperTradingPreviewData,
  PerformanceOutcomesData,
  PortfolioCoverageData,
  RecommendationDetailData,
  RecommendationListData,
  RemediationTicketsData,
  SourceDocumentDetailData,
  StockDetailData,
  StockListData,
  ThemeDetailData,
  ThesisDetailData,
  TradingReadinessData,
} from "./types";
import { normalizeAiEvidenceDetailPayload } from "./frontend-normalizers-ai-evidence";
import { normalizeMarketMapPayload } from "./frontend-normalizers-market";
import { normalizeDataHealthPayload } from "./frontend-normalizers-operations";
import { normalizePaperTradingPreviewPayload } from "./frontend-normalizers-paper";
import { normalizePerformanceOutcomesPayload } from "./frontend-normalizers-performance";
import { ensureArray, ensureRecord, isRecord, type MutableRecord, withDefault } from "./frontend-normalizer-utils";

const DEFAULT_FIXTURE_BASE_URL = "http://127.0.0.1:8765";

export class FrontendApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly path: string,
  ) {
    super(message);
    this.name = "FrontendApiError";
  }
}

function fixtureBaseUrl(): string {
  return (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? DEFAULT_FIXTURE_BASE_URL).replace(/\/$/, "");
}

export async function fetchFrontendPayload<TData>(path: string, options: { signal?: AbortSignal } = {}): Promise<ApiResponse<TData>> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const readToken = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  if (readToken) {
    headers.Authorization = `Bearer ${readToken}`;
  }

  const response = await fetch(`${fixtureBaseUrl()}${path}`, {
    cache: "no-store",
    ...(options.signal ? { signal: options.signal } : {}),
    headers,
  });

  if (!response.ok) {
    let message = `Frontend fixture request failed for ${path}`;
    try {
      const payload = (await response.json()) as { error?: { message?: string } };
      message = payload.error?.message ?? message;
    } catch {
      message = `${message}: HTTP ${response.status}`;
    }
    throw new FrontendApiError(message, response.status, path);
  }

  const payload = (await response.json()) as ApiResponse<TData>;
  return normalizeFrontendPayload(path, payload) as ApiResponse<TData>;
}

function dataRecord(payload: ApiResponse<unknown>) {
  if (!isRecord(payload.data)) {
    payload.data = {} as never;
  }
  return payload.data as MutableRecord;
}

function recommendationIdFromPath(path: string): string {
  const rawId = path.split("/").pop() ?? "";
  try {
    return decodeURIComponent(rawId);
  } catch (error) {
    if (error instanceof URIError) {
      return rawId;
    }
    throw error;
  }
}

function recommendationSymbolFromId(recommendationId: string): string | null {
  const match = recommendationId.match(/^([A-Z][A-Z0-9.]{0,9})(?:-\d{4}-\d{2}-\d{2}|-|$)/);
  return match ? match[1] : null;
}

function defaultEvidenceReview() {
  return {
    quality_status: "not_available",
    summary: {
      pass_count: 0,
      warning_count: 0,
      blocked_count: 0,
      source_event_count: 0,
      performance_evidence_count: 0,
      ai_evidence_component_count: 0,
      market_or_rank_provenance_count: 0,
    },
    gates: [],
  };
}

function defaultValuationTargetRange(symbol: string) {
  return {
    status: "unavailable",
    symbol,
    as_of_date: "",
    valuation_as_of_date: "",
    method_count: 0,
    base_price: null,
    target_low: null,
    target_base: null,
    target_high: null,
    upside_low: null,
    upside_base: null,
    upside_high: null,
    margin_of_safety: null,
    confidence: null,
    currency_code: "USD",
    methods: [],
    summary: "밸류에이션 원천 데이터가 아직 충분히 연결되지 않았다.",
    valuation_quality: {
      status: "unavailable",
      label: "가정 품질 미수집",
      method_coverage: 0,
      expected_method_count: 0,
      missing_methods: [],
      data_gap_count: 0,
      warning_count: 0,
      confidence: null,
      confidence_label: "미수집",
      order_boundary: "read_only_no_order",
    },
    score_policy: "recommendation_weights_unchanged",
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  };
}

function defaultFinancialStatementModel(symbol: string) {
  return {
    status: "unavailable",
    symbol,
    summary: "재무제표 정규화 데이터가 아직 충분히 연결되지 않았다.",
    latest_period_end: "",
    statement_scope: "unknown",
    metric_count: 0,
    computed_metric_count: 0,
    data_gap_count: 0,
    metrics: [],
    sections: [],
    share_count: {
      latest_period_end: "",
      share_count_change_pct: null,
    },
    source_data_blocker: null,
  };
}

function defaultProfessionalSourceGuardrail() {
  return {
    status: "not_available",
    blocked: false,
    professional_decision_use_allowed: false,
    paper_validation_input_allowed: false,
    blocker_code: "",
    blocker_label: "",
    source_data_blocker: null,
    summary: "전문 원천 상태가 아직 충분히 연결되지 않았다.",
    next_action: "수집 상태와 원천 문서 연결 상태를 확인한다.",
    score_policy: "recommendation_weights_unchanged",
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
    source_run_id: "",
  };
}

function defaultProfessionalDecisionWaterfall(symbol: string, recommendation = "unknown", score: number | null = null) {
  return {
    status: "not_available",
    summary: "전문 판단 흐름 데이터가 아직 충분히 연결되지 않았다. 이 화면에서는 주문을 만들지 않는다.",
    symbol,
    as_of_date: "",
    recommendation,
    score,
    score_component_count: 0,
    paper_validation_input_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
    score_policy: "recommendation_weights_unchanged",
    steps: [],
  };
}

function defaultProfessionalEvidenceAudit(symbol: string, recommendationId = "", recommendation = "unknown") {
  return {
    status: "not_available",
    title: "전문 감사 대기",
    summary: "재무·밸류에이션·뉴스·사이클 근거 감사 데이터가 아직 충분히 연결되지 않았다.",
    next_action: "원천 데이터, 추천 상세, 가상 매매 검증 연결 상태를 확인한다.",
    recommendation_id: recommendationId,
    symbol,
    as_of_date: "",
    recommendation,
    score: null,
    product_type: "stock",
    coverage_ratio: 0,
    available_layer_count: 0,
    partial_layer_count: 0,
    expected_layer_count: 0,
    missing_layer_count: 0,
    blocked_layer_count: 0,
    pending_layer_count: 0,
    missing_layers: [],
    missing_layer_labels: [],
    layer_checks: [],
    source_blocker: {
      blocked: false,
      blocker_code: "",
      blocker_label: "",
      summary: "",
      next_action: "",
      source_run_id: "",
    },
    paper_validation_status: "not_available",
    paper_validation_input_allowed: false,
    professional_decision_status: "not_available",
    evidence_quality_status: "not_available",
    blocked_evidence_gate_count: 0,
    warning_evidence_gate_count: 0,
    holding_review_status: "not_available",
    score_policy: "recommendation_weights_unchanged",
    recommendation_scoring_mutated: false,
    automatic_weight_change_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  };
}

function defaultRebalanceCandidateReview() {
  return {
    status: "not_available",
    candidate_count: 0,
    decision_counts: {},
    benchmark_code: "SPY",
    benchmark_source: "",
    source_type: "",
    source_as_of_date: "",
    active_share: null,
    composition_coverage_weight: 0,
    review_threshold_active_weight: 0,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
    candidates: [],
    next_actions: [],
  };
}

function defaultPositionSizingReview() {
  return {
    status: "not_available",
    review_required_count: 0,
    reduce_review_count: 0,
    add_blocked_until_evidence_count: 0,
    watch_small_position_count: 0,
    min_rebalance_target_weight: null,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
    candidates: [],
  };
}

function defaultGuardrails() {
  return {
    recommendation_scoring_mutated: false,
    benchmark_definition_mutated: false,
    portfolio_position_mutated: false,
    automatic_rebalance_allowed: false,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
  };
}

function defaultReviewDecisionHistory() {
  return {
    status: "not_available",
    eval_run_id: "",
    created_at: "",
    eval_name: "",
    dataset_version: "",
    as_of_date: "",
    portfolio_name: "",
    source_portfolio_coverage_as_of_date: "",
    coverage_measurement_end_date: "",
    decision_status: "not_available",
    decision_count: 0,
    review_required_count: 0,
    benchmark_decision_count: 0,
    position_sizing_decision_count: 0,
    decision_counts: {},
    attention_required: false,
    managed_review_status: "not_available",
    managed_review_reason: "",
    top_decision: null,
    latest_decisions: [],
    guardrails: defaultGuardrails(),
    next_action: "",
  };
}

function defaultReviewDecisionFeedback() {
  return {
    status: "not_available",
    eval_run_id: "",
    created_at: "",
    eval_name: "",
    dataset_version: "",
    as_of_date: "",
    portfolio_name: "",
    source_history_eval_run_id: "",
    source_history_as_of_date: "",
    min_horizon_days: 30,
    history_age_days: 0,
    feedback_status: "not_available",
    decision_count: 0,
    too_early_count: 0,
    validated_count: 0,
    contradicted_count: 0,
    needs_more_data_count: 0,
    status_counts: {},
    paper_validation: {
      paper_validation_run_id: "",
      validation_date: "",
      status: "not_available",
      recommendation_count: 0,
      conflict_count: 0,
      approved_action_count: 0,
    },
    top_feedback: null,
    latest_items: [],
    guardrails: defaultGuardrails(),
    next_action: "",
  };
}

function defaultReviewFeedbackCalibration() {
  return {
    status: "not_available",
    eval_run_id: "",
    created_at: "",
    eval_name: "",
    dataset_version: "",
    as_of_date: "",
    portfolio_name: "",
    lookback_days: 90,
    min_feedback_runs: 3,
    min_mature_decisions: 10,
    max_contradiction_rate: 0.2,
    calibration_status: "not_available",
    maturity_status: "not_available",
    feedback_run_count: 0,
    decision_count: 0,
    mature_decision_count: 0,
    too_early_count: 0,
    validated_count: 0,
    contradicted_count: 0,
    needs_more_data_count: 0,
    contradiction_rate: 0,
    validated_rate: 0,
    feedback_run_gap: 3,
    mature_decision_gap: 10,
    estimated_maturity_date: "",
    days_until_maturity: null,
    attention_required: false,
    managed_wait: true,
    managed_gate_status: "not_available",
    managed_gate_reason: "성과 성숙 평가 데이터가 아직 연결되지 않았다.",
    weight_review_blocked: true,
    weight_review_block_reason: "성과 표본 미확인",
    status_counts: {},
    family_summaries: [],
    decision_type_summaries: [],
    symbol_summaries: [],
    latest_feedback_runs: [],
    guardrails: defaultGuardrails(),
    next_action: "",
    next_calibration_action: "",
  };
}

function defaultReviewFeedbackCadence() {
  return {
    status: "not_available",
    cadence_status: "not_available",
    label: "성과 평가 주기 대기",
    reason: "포트폴리오 사후평가 주기 정보가 아직 연결되지 않았다.",
    should_run_now: false,
    min_horizon_days: 30,
    evidence: { history_age_days: 0 },
    feedback: { eval_run_id: "", feedback_status: "not_available" },
    calibration: { eval_run_id: "" },
    order_boundary: "read_only_no_order",
    broker_submit_allowed: false,
  };
}

function defaultReviewFeedbackActionRouter() {
  return {
    status: "not_available",
    action_status: "no_op_not_available",
    route_action: "wait",
    cadence_status: "not_available",
    source_cadence_eval_run_id: "",
    reason: "실행 라우터 결과가 아직 연결되지 않았다.",
    child_runner: {
      executed: false,
      report_name: "",
      eval_run_id: "",
    },
    order_boundary: "read_only_no_order",
    broker_submit_allowed: false,
    next_action: "성과 측정 주기와 실행 라우터 연결 상태를 확인한다.",
  };
}

function defaultConcentration() {
  return {
    status: "not_available",
    max_sector_weight: null,
    max_theme_weight: null,
    max_unclassified_weight: null,
    sector_exposures: [],
    theme_exposures: [],
    unclassified_weight: 0,
    unclassified_symbols: [],
    over_limit_count: 0,
    review_reasons: [],
  };
}

function defaultPortfolioRiskBudgetGuardrail() {
  return {
    status: "not_available",
    eval_run_id: null,
    as_of_date: "",
    effective_snapshot_date: "",
    risk_gate_decision: "not_available",
    paper_validation_input_allowed: false,
    blocking_reasons: [],
    warning_reasons: ["risk_budget_not_available"],
    benchmark_drift: {
      drift_calculated: false,
      benchmark_code: "SPY",
      active_share: null,
      benchmark_source: "",
    },
    rebalance_candidate_review: defaultRebalanceCandidateReview(),
  };
}

function defaultTossInvestOrderReadiness() {
  return {
    status: "missing",
    latest_status: "missing",
    latest_run_id: null,
    finished_at: "",
    portfolio_name: "Toss Real Readonly",
    base_currency: "KRW",
    buying_power: [],
    sellable_quantities: [],
    sellable_quantity_count: 0,
    commission_summary: [],
    stock_warnings: [],
    stock_warning_symbol_count: 0,
    market_microdata: [],
    market_microdata_symbol_count: 0,
    order_history: {
      status: "missing",
      open_order_count: 0,
      closed_order_count: 0,
      order_count: 0,
      secret_free: true,
    },
    provider_http_status: null,
    provider_error: "",
    provider_error_description: "",
    config_gap: "",
    operator_action: "",
    submit_adapter_status: "disabled_stub",
    order_submit_attempted: false,
    submitted_to_broker: false,
    broker_submit_allowed: false,
    automatic_order_allowed: false,
    order_boundary: "read_only_no_order",
    secret_free: true,
  };
}

function defaultPortfolioCurrencyConversion(baseCurrency = "USD") {
  return {
    base_currency: baseCurrency,
    native_currencies: [baseCurrency],
    fx_converted_position_count: 0,
    fx_rate_providers: [],
    latest_fx_conversion_timestamp: "",
  };
}

function defaultLifecycle(symbol: string, summary = "") {
  return {
    source: "read_only_fallback",
    equity_research_artifact_id: null,
    buy_case: {
      symbol,
      summary,
      core_claims: [],
    },
    catalysts: [],
    risks: [],
    invalidation_conditions: [],
    valuation: {
      base_case: null,
      upside_case: null,
      downside_case: null,
      margin_of_safety_view: null,
      confidence: null,
      raw: {},
      has_view: false,
    },
    review_cadence: {
      latest_review_action: "not_available",
      risk_level: "medium",
      reviewed_at: "",
      next_review_date: "",
      summary: "",
    },
    readiness: {
      status: "partial",
      missing_items: ["lifecycle_not_available"],
      core_claim_count: 0,
      catalyst_count: 0,
      risk_count: 0,
      invalidation_count: 0,
      has_valuation_view: false,
      has_next_review_date: false,
    },
  };
}

function defaultProfessionalLifecycleGates() {
  return {
    status: "partial",
    summary: "전문 투자 논리 확인 조건 데이터가 아직 충분히 연결되지 않았다.",
    gate_count: 0,
    pass_count: 0,
    warning_count: 0,
    blocked_count: 0,
    latest_evidence_at: null,
    latest_reviewed_at: null,
    next_review_date: null,
    automatic_order_allowed: false,
    broker_submit_allowed: false,
    order_boundary: "read_only_no_order",
    gates: [],
  };
}

function normalizeFrontendPayload<TData>(path: string, payload: ApiResponse<TData>) {
  const mutablePayload = payload as ApiResponse<unknown>;
  const data = dataRecord(mutablePayload);
  if (path.startsWith("/api/recommendations/")) {
    normalizeRecommendationDetail(data, path);
  } else if (path === "/api/recommendations") {
    normalizeRecommendationList(data);
  } else if (path.startsWith("/api/theses/")) {
    normalizeThesisDetail(data);
  } else if (path.startsWith("/api/stocks/")) {
    normalizeStockDetail(data);
  } else if (path.startsWith("/api/portfolio/") && path.includes("/coverage")) {
    normalizePortfolioCoverage(data);
  } else if (path === "/api/trading/readiness") {
    normalizeTradingReadiness(data);
  } else if (path === "/api/paper-trading/preview") {
    normalizePaperTradingPreviewPayload(data);
  } else if (path === "/api/data-health") {
    normalizeDataHealthPayload(data);
  } else if (path.startsWith("/api/market-map")) {
    normalizeMarketMapPayload(data);
  } else if (path.startsWith("/api/performance/")) {
    normalizePerformanceOutcomesPayload(data);
  } else if (path.startsWith("/api/ai-evidence/")) {
    normalizeAiEvidenceDetailPayload(data);
  }
  return mutablePayload as ApiResponse<TData>;
}

function normalizeRecommendationList(data: MutableRecord) {
  const summary = ensureRecord(data, "summary");
  for (const key of [
    "macro_flow_evidence_recommendation_count",
    "decision_review_ready_count",
    "paper_validation_pending_count",
    "decision_blocked_count",
    "order_blocked_count",
    "evidence_quality_ready_count",
    "evidence_quality_gap_count",
    "evidence_quality_source_blocked_count",
  ]) {
    withDefault(summary, key, 0);
  }
  withDefault(summary, "average_score", null);
  for (const rawRow of ensureArray(data, "recommendations")) {
    if (!isRecord(rawRow)) {
      continue;
    }
    const row = rawRow;
    const evidence = ensureRecord(row, "evidence");
    withDefault(evidence, "macro_flow_component_count", 0);
    withDefault(evidence, "macro_flow_evidence_count", 0);
    withDefault(evidence, "score_component_count", 0);
    withDefault(evidence, "ai_or_event_component_count", 0);
    withDefault(evidence, "market_or_rank_component_count", 0);
    withDefault(evidence, "quality_status", "not_available");
    withDefault(evidence, "primary_evidence_id", null);

    const evidenceQuality = ensureRecord(row, "evidence_quality");
    withDefault(evidenceQuality, "status", "not_available");
    withDefault(evidenceQuality, "title", "근거 감사 대기");
    withDefault(evidenceQuality, "summary", "전문 근거 감사 데이터가 아직 충분히 연결되지 않았다.");
    withDefault(evidenceQuality, "product_type", "stock");
    withDefault(evidenceQuality, "coverage_ratio", null);
    withDefault(evidenceQuality, "available_layer_count", 0);
    withDefault(evidenceQuality, "expected_layer_count", 0);
    withDefault(evidenceQuality, "missing_layer_count", 0);
    withDefault(evidenceQuality, "blocked_layer_count", 0);
    withDefault(evidenceQuality, "pending_layer_count", 0);
    withDefault(evidenceQuality, "missing_layers", []);
    withDefault(evidenceQuality, "missing_layer_labels", []);
    withDefault(evidenceQuality, "source_blocker", {
      blocked: false,
      blocker_code: "",
      blocker_label: "",
      summary: "",
    });
    withDefault(evidenceQuality, "paper_validation_status", "not_available");
    withDefault(evidenceQuality, "score_policy", "recommendation_weights_unchanged");
    withDefault(evidenceQuality, "automatic_weight_change_allowed", false);
    withDefault(evidenceQuality, "automatic_order_allowed", false);
    withDefault(evidenceQuality, "broker_submit_allowed", false);
    withDefault(evidenceQuality, "order_boundary", "read_only_no_order");

    const decisionBoundary = ensureRecord(row, "decision_boundary");
    withDefault(decisionBoundary, "status", row.linked_thesis_id ? "paper_validation_pending" : "blocked_missing_thesis");
    withDefault(decisionBoundary, "reason", "최신 추천 결정 경계가 아직 충분히 연결되지 않았다.");
    withDefault(decisionBoundary, "paper_validation_input_allowed", false);
    withDefault(decisionBoundary, "automatic_order_allowed", false);
    withDefault(decisionBoundary, "broker_submit_allowed", false);
    withDefault(decisionBoundary, "order_boundary", "read_only_no_order");
  }
}

function normalizeRecommendationDetail(data: MutableRecord, path: string) {
  const pathRecommendationId = recommendationIdFromPath(path);
  const recommendationId =
    typeof data.recommendation_id === "string" && data.recommendation_id.length > 0
      ? data.recommendation_id
      : pathRecommendationId;
  const symbol =
    typeof data.symbol === "string" && data.symbol.length > 0 && data.symbol !== "UNKNOWN"
      ? data.symbol
      : (recommendationSymbolFromId(recommendationId) ?? "UNKNOWN");
  const recommendation = typeof data.recommendation === "string" ? data.recommendation : "unknown";
  data.recommendation_id = recommendationId;
  data.symbol = symbol;
  withDefault(data, "currency_code", "USD");
  withDefault(data, "equity_research", null);
  withDefault(data, "industry_competitive_position", null);
  withDefault(data, "financial_statement_model", defaultFinancialStatementModel(symbol));
  withDefault(data, "valuation_target_range", defaultValuationTargetRange(symbol));
  withDefault(data, "fund_instrument_analysis", null);
  withDefault(data, "professional_source_guardrail", defaultProfessionalSourceGuardrail());
  withDefault(data, "market_correlations", []);
  withDefault(data, "professional_decision_waterfall", defaultProfessionalDecisionWaterfall(symbol, recommendation, typeof data.score === "number" ? data.score : null));
  withDefault(data, "professional_evidence_audit", defaultProfessionalEvidenceAudit(symbol, recommendationId, recommendation));
  withDefault(data, "evidence_trace", {
    symbol,
    as_of_date: typeof data.as_of_date === "string" ? data.as_of_date : "",
    direct_news_or_ai: {
      status: "not_available",
      evidence_id: null,
      event_id: null,
      ai_evidence_id: null,
      title: null,
      event_at: "",
      impact_direction: "unknown",
      impact_strength: null,
      confidence: null,
      rationale: null,
    },
    macro_flow: {
      status: "not_available",
      propagated_impact_count: 0,
      source_run_id: null,
      recent_flows: [],
    },
    holding_review: {
      status: "not_available",
      portfolio_name: "",
      portfolio_review_id: null,
      review_item_id: null,
      review_date: null,
      review_source: null,
      risk_level: null,
      source_run_id: null,
      action: "not_available",
      reason: null,
      priority: null,
      health_score: null,
      current_weight: null,
      recommended_weight: null,
      weight_gap: null,
      market_value: null,
      position_snapshot_date: null,
      position_source_run_id: null,
      position_linked_thesis_id: null,
    },
  });
  withDefault(data, "evidence_review", defaultEvidenceReview());
  withDefault(data, "outcome", {
    measurement_end_date: "",
    absolute_return: 0,
    benchmark_return: 0,
    alpha: 0,
    label: "unmeasured",
  });
}

function normalizeThesisDetail(data: MutableRecord) {
  const symbol = typeof data.symbol === "string" ? data.symbol : "UNKNOWN";
  const latestReview = ensureRecord(data, "latest_review");
  withDefault(latestReview, "review_id", "");
  withDefault(latestReview, "action", "not_available");
  withDefault(latestReview, "risk_level", "medium");
  withDefault(latestReview, "reviewed_at", "");
  withDefault(latestReview, "summary", "");
  withDefault(latestReview, "change_notes", "");
  withDefault(latestReview, "next_review_date", "");
  withDefault(data, "currency_code", "USD");
  withDefault(data, "lifecycle", defaultLifecycle(symbol, typeof data.summary === "string" ? data.summary : ""));
  withDefault(data, "professional_lifecycle_gates", defaultProfessionalLifecycleGates());
  withDefault(data, "valuation_target_range", defaultValuationTargetRange(symbol));
  withDefault(data, "evidence_review", defaultEvidenceReview());
}

function normalizeStockDetail(data: MutableRecord) {
  const symbol = typeof data.symbol === "string" ? data.symbol : "UNKNOWN";
  withDefault(data, "candles", Array.isArray(data.price_bars) ? data.price_bars : []);
  withDefault(data, "market_data_provider", {
    canonical_provider: "missing",
    provider_source_run_id: null,
    latest_trade_date: "",
    freshness_status: "missing",
    toss_shadow_status: "missing",
    toss_shadow_reason: "",
    canonical_promotion_allowed: false,
    order_boundary: "read_only_no_order",
    analysis_price_source: {
      role: "analysis_reference",
      label: "분석 기준 가격",
      provider: "missing",
      source_run_id: null,
      latest_trade_date: "",
      freshness_status: "missing",
      status: "missing",
      reason: "",
      reason_label: "추천·사이클·성과 계산 기준으로 쓰는 글로벌 가격 데이터다.",
      used_for_scoring: true,
      used_for_cycle: true,
      used_for_performance: true,
      used_for_account: false,
      used_for_execution: false,
      price_basis_note: "장기 비교와 분석 일관성을 위해 쓰는 기준 가격이다.",
    },
    broker_price_source: {
      role: "broker_reference",
      label: "토스증권 브로커 데이터",
      provider: "tossinvest",
      source_run_id: null,
      latest_trade_date: "",
      freshness_status: "missing",
      status: "missing",
      status_label: "토스증권 가격 대기",
      reason: "",
      reason_label: "비교 사유 미기록",
      used_for_scoring: false,
      used_for_cycle: false,
      used_for_performance: false,
      used_for_account: false,
      used_for_execution: false,
      price_basis_note: "실제 증권사 화면과 계좌 현실을 확인하는 참고 가격이며 추천 점수에는 아직 반영하지 않는다.",
    },
    validation_price_source: {
      role: "validation_price",
      label: "검증 중 가격",
      provider: "tossinvest",
      source_run_id: null,
      latest_trade_date: "",
      freshness_status: "missing",
      status: "missing",
      status_label: "토스증권 가격 대기",
      reason: "",
      reason_label: "비교 사유 미기록",
      used_for_scoring: false,
      used_for_cycle: false,
      used_for_performance: false,
      used_for_account: false,
      used_for_execution: false,
      price_basis_note: "분석 기준 가격과 비교해 가격 기준 차이, 미완성 일봉, 누락 여부를 분류한다.",
    },
    used_for_scoring: true,
    used_for_account: false,
    used_for_execution: false,
    price_basis_note: "분석 계산은 글로벌 기준 가격을 쓰고, 토스 데이터는 브로커 현실 확인과 품질 감사에 사용한다.",
  });
  withDefault(data, "toss_provider_evidence", {
    status: "missing",
    status_label: "토스증권 가격 대기",
    source_role: "broker_reference",
    source_role_label: "토스증권 브로커 데이터",
    used_for_scoring: false,
    used_for_account: false,
    used_for_execution: false,
    price_basis_note: "토스증권에서 실제 투자자가 보는 가격과 수집 근거를 확인한다. 추천 점수와 사이클 계산에는 아직 직접 반영하지 않는다.",
    latest_trade_date: "",
    latest_close: null,
    latest_adjusted_close: null,
    latest_volume: 0,
    source_run_id: null,
    observed_at: "",
    comparison: {
      status: "missing",
      status_label: "토스 비교 데이터 없음",
      reason: "",
      reason_label: "비교 사유 미기록",
      comparison_basis_label: "분석 기준 가격과 토스증권 브로커 가격 비교",
      comparison_date: "",
      canonical_provider: "",
      analysis_provider: "",
      compared_provider: "tossinvest",
      broker_provider: "tossinvest",
      matched_bar_count: 0,
      missing_canonical_count: 0,
      missing_compared_count: 0,
      max_close_diff_bps: null,
      median_close_diff_bps: null,
    },
  });
  const provider = data.market_data_provider as MutableRecord;
  const analysisProvider = typeof provider.canonical_provider === "string" ? provider.canonical_provider : "missing";
  const providerSourceRunId = typeof provider.provider_source_run_id === "string" ? provider.provider_source_run_id : null;
  const providerLatestTradeDate = typeof provider.latest_trade_date === "string" ? provider.latest_trade_date : "";
  const providerFreshness = typeof provider.freshness_status === "string" ? provider.freshness_status : "missing";
  const tossStatus = typeof provider.toss_shadow_status === "string" ? provider.toss_shadow_status : "missing";
  const tossReason = typeof provider.toss_shadow_reason === "string" ? provider.toss_shadow_reason : "";
  withDefault(provider, "analysis_price_source", {
    role: "analysis_reference",
    label: "분석 기준 가격",
    provider: analysisProvider,
    source_run_id: providerSourceRunId,
    latest_trade_date: providerLatestTradeDate,
    freshness_status: providerFreshness,
    status: providerFreshness,
    reason: "",
    reason_label: "추천·사이클·성과 계산 기준으로 쓰는 글로벌 가격 데이터다.",
    used_for_scoring: true,
    used_for_cycle: true,
    used_for_performance: true,
    used_for_account: false,
    used_for_execution: false,
    price_basis_note: "장기 비교와 분석 일관성을 위해 쓰는 기준 가격이다.",
  });
  withDefault(provider, "broker_price_source", {
    role: "broker_reference",
    label: "토스증권 브로커 데이터",
    provider: "tossinvest",
    source_run_id: null,
    latest_trade_date: "",
    freshness_status: tossStatus,
    status: tossStatus,
    status_label: "토스증권 가격 검증 중",
    reason: tossReason,
    reason_label: tossReason || "비교 사유 미기록",
    used_for_scoring: false,
    used_for_cycle: false,
    used_for_performance: false,
    used_for_account: tossStatus !== "missing",
    used_for_execution: false,
    price_basis_note: "실제 증권사 화면과 계좌 현실을 확인하는 참고 가격이며 추천 점수에는 아직 반영하지 않는다.",
  });
  withDefault(provider, "validation_price_source", {
    role: "validation_price",
    label: "검증 중 가격",
    provider: "tossinvest",
    source_run_id: null,
    latest_trade_date: "",
    freshness_status: tossStatus,
    status: tossStatus,
    status_label: "토스증권 가격 검증 중",
    reason: tossReason,
    reason_label: tossReason || "비교 사유 미기록",
    used_for_scoring: false,
    used_for_cycle: false,
    used_for_performance: false,
    used_for_account: false,
    used_for_execution: false,
    price_basis_note: "분석 기준 가격과 비교해 가격 기준 차이, 미완성 일봉, 누락 여부를 분류한다.",
  });
  withDefault(provider, "used_for_scoring", true);
  withDefault(provider, "used_for_account", tossStatus !== "missing");
  withDefault(provider, "used_for_execution", false);
  withDefault(
    provider,
    "price_basis_note",
    "분석 계산은 글로벌 기준 가격을 쓰고, 토스 데이터는 브로커 현실 확인과 품질 감사에 사용한다.",
  );
  const tossEvidence = data.toss_provider_evidence as MutableRecord;
  const tossComparison = ensureRecord(tossEvidence, "comparison");
  withDefault(tossEvidence, "status_label", tossEvidence.status === "available" ? "토스증권 가격 수집됨" : "토스증권 가격 대기");
  withDefault(tossEvidence, "source_role", "broker_reference");
  withDefault(tossEvidence, "source_role_label", "토스증권 브로커 데이터");
  withDefault(tossEvidence, "used_for_scoring", false);
  withDefault(tossEvidence, "used_for_account", tossEvidence.status === "available");
  withDefault(tossEvidence, "used_for_execution", false);
  withDefault(
    tossEvidence,
    "price_basis_note",
    "토스증권에서 실제 투자자가 보는 가격과 수집 근거를 확인한다. 추천 점수와 사이클 계산에는 아직 직접 반영하지 않는다.",
  );
  withDefault(tossComparison, "status_label", "토스 비교 데이터 없음");
  withDefault(tossComparison, "reason_label", "비교 사유 미기록");
  withDefault(tossComparison, "comparison_basis_label", "분석 기준 가격과 토스증권 브로커 가격 비교");
  withDefault(tossComparison, "analysis_provider", tossComparison.canonical_provider || "");
  withDefault(tossComparison, "broker_provider", tossComparison.compared_provider || "tossinvest");
  withDefault(data, "freshness_status", provider.freshness_status || "missing");
  withDefault(data, "equity_research", null);
  withDefault(data, "industry_competitive_position", null);
  withDefault(data, "financial_statement_model", defaultFinancialStatementModel(symbol));
  withDefault(data, "valuation_target_range", defaultValuationTargetRange(symbol));
  withDefault(data, "fund_instrument_analysis", null);
  withDefault(data, "professional_source_guardrail", defaultProfessionalSourceGuardrail());
  withDefault(data, "market_correlations", []);
  withDefault(data, "macro_flow_impacts", []);
}

function normalizePortfolioCoverage(data: MutableRecord) {
  withDefault(data, "base_currency", "USD");
  withDefault(data, "allocation_policy", {
    policy_id: "",
    policy_name: "기본 읽기 전용 정책",
    status: "not_available",
    policy_scope: "portfolio",
    max_single_position_weight: null,
    min_rebalance_target_weight: null,
    valid_from: "",
    valid_to: "",
    rationale: "최신 배분 정책 데이터가 아직 충분히 연결되지 않았다.",
  });
  withDefault(data, "currency_conversion", defaultPortfolioCurrencyConversion(String(data.base_currency || "USD")));
  const riskBudget = ensureRecord(data, "risk_budget");
  withDefault(riskBudget, "status", "not_available");
  withDefault(riskBudget, "max_single_position_weight", null);
  withDefault(riskBudget, "min_rebalance_target_weight", null);
  withDefault(riskBudget, "max_sector_weight", null);
  withDefault(riskBudget, "max_theme_weight", null);
  withDefault(riskBudget, "max_unclassified_weight", null);
  withDefault(riskBudget, "largest_position_symbol", null);
  withDefault(riskBudget, "largest_position_weight", null);
  withDefault(riskBudget, "over_single_position_limit_count", 0);
  withDefault(riskBudget, "below_rebalance_floor_count", 0);
  withDefault(riskBudget, "cash_weight", null);
  withDefault(riskBudget, "invested_weight", null);
  withDefault(riskBudget, "concentration", defaultConcentration());
  withDefault(riskBudget, "rebalance_priorities", []);
  withDefault(riskBudget, "rebalance_candidate_review", defaultRebalanceCandidateReview());
  withDefault(riskBudget, "position_sizing_review", defaultPositionSizingReview());
  withDefault(riskBudget, "review_decision_history", defaultReviewDecisionHistory());
  withDefault(riskBudget, "review_decision_feedback", defaultReviewDecisionFeedback());
  withDefault(riskBudget, "review_feedback_calibration", defaultReviewFeedbackCalibration());
  withDefault(riskBudget, "review_feedback_cadence", defaultReviewFeedbackCadence());
  withDefault(riskBudget, "review_feedback_action_router", defaultReviewFeedbackActionRouter());
  withDefault(riskBudget, "review_reasons", []);
  for (const rawPosition of ensureArray(data, "positions")) {
    if (!isRecord(rawPosition)) {
      continue;
    }
    withDefault(rawPosition, "position_size_status", "not_available");
    withDefault(rawPosition, "base_currency", data.base_currency || "USD");
    withDefault(rawPosition, "native_currency_code", rawPosition.base_currency || data.base_currency || "USD");
    withDefault(rawPosition, "market_price", null);
    withDefault(rawPosition, "market_value", null);
    withDefault(rawPosition, "market_price_native", null);
    withDefault(rawPosition, "market_value_native", null);
    withDefault(rawPosition, "cost_basis", null);
    withDefault(rawPosition, "cost_basis_native", null);
    withDefault(rawPosition, "unrealized_pnl", null);
    withDefault(rawPosition, "unrealized_pnl_native", null);
    withDefault(rawPosition, "fx_rate_to_base", null);
    withDefault(rawPosition, "fx_rate_provider", "");
    withDefault(rawPosition, "fx_conversion_timestamp", "");
    withDefault(rawPosition, "currency_conversion_note", "");
    withDefault(rawPosition, "max_single_position_weight", null);
    withDefault(rawPosition, "min_rebalance_target_weight", null);
    withDefault(rawPosition, "weight_to_single_position_limit", null);
    withDefault(rawPosition, "position_size_note", "");
  }
}

function normalizeTradingReadiness(data: MutableRecord) {
  withDefault(data, "execution_boundary", {
    paper_portfolio_name: "Long Term Paper",
    live_account_portfolio_name: "Toss Real Readonly",
    live_account_provider: "tossinvest",
    submit_adapter_status: "disabled_stub",
    broker_submit_allowed: false,
    submitted_to_broker: false,
    order_boundary: "read_only_no_order",
  });
  withDefault(data, "portfolio_risk_budget_guardrail", defaultPortfolioRiskBudgetGuardrail());
  withDefault(data, "tossinvest_order_readiness", defaultTossInvestOrderReadiness());
}

export async function getCockpitSnapshot() {
  const [dashboard, tickets, health] = await Promise.all([
    fetchFrontendPayload<DailyCockpitData>("/api/dashboard/today"),
    fetchFrontendPayload<RemediationTicketsData>("/api/remediation-tickets?status=open"),
    fetchFrontendPayload<DataHealthData>("/api/data-health"),
  ]);

  return { dashboard, tickets, health };
}

export function getDashboardToday() {
  return fetchFrontendPayload<DailyCockpitData>("/api/dashboard/today");
}

export function getRemediationTickets() {
  return fetchFrontendPayload<RemediationTicketsData>("/api/remediation-tickets?status=open");
}

export function getDataHealth() {
  return fetchFrontendPayload<DataHealthData>("/api/data-health");
}

export async function getAiAgentRegistry() {
  try {
    return await fetchFrontendPayload<AiAgentRegistryData>("/api/admin/ai-agents");
  } catch (error) {
    if (error instanceof FrontendApiError && error.status === 404) {
      return buildAiAgentRegistryFallback();
    }
    throw error;
  }
}

export function getStocks() {
  return fetchFrontendPayload<StockListData>("/api/stocks");
}

export function getStockDetail(symbol: string) {
  return fetchFrontendPayload<StockDetailData>(`/api/stocks/${encodeURIComponent(symbol)}`);
}

export async function getAiEvidenceNeighborhood(symbol: string) {
  const path = `/api/ai/evidence-neighborhoods/${encodeURIComponent(symbol)}`;
  try {
    return await fetchFrontendPayload<AiEvidenceNeighborhoodData>(path);
  } catch (error) {
    if (error instanceof FrontendApiError && error.status === 404) {
      return buildAiEvidenceNeighborhoodFallback(symbol);
    }
    throw error;
  }
}

export function getAiNewsClusters({
  asOfDate = currentIsoDate(),
  themeKey,
  symbol,
  limit = 4,
}: {
  asOfDate?: string;
  themeKey?: string;
  symbol?: string;
  limit?: number;
} = {}) {
  const params = new URLSearchParams({
    asOfDate,
    limit: String(limit),
  });
  if (themeKey) {
    params.set("themeKey", themeKey);
  }
  if (symbol) {
    params.set("symbol", symbol);
  }
  return fetchFrontendPayload<AiNewsClusterListData>(`/api/ai/news-clusters?${params.toString()}`);
}

export function getPaperTradingPreview() {
  return fetchFrontendPayload<PaperTradingPreviewData>("/api/paper-trading/preview");
}

export function getTradingReadiness() {
  return fetchFrontendPayload<TradingReadinessData>("/api/trading/readiness");
}

export function getCycleStates() {
  const query = new URLSearchParams({ asOfDate: currentIsoDate() });
  return fetchFrontendPayload<CycleStateListData>(`/api/cycles?${query.toString()}`);
}

export async function getCycleMap() {
  const query = new URLSearchParams({ asOfDate: currentIsoDate() });
  const path = `/api/cycle-map?${query.toString()}`;
  try {
    return await fetchFrontendPayload<CycleMapData>(path);
  } catch (error) {
    if (error instanceof FrontendApiError && error.status === 404) {
      return buildCycleMapFallback();
    }
    throw error;
  }
}

export async function getMarketMap() {
  const query = new URLSearchParams({ asOfDate: currentIsoDate() });
  const path = `/api/market-map?${query.toString()}`;
  try {
    return await fetchFrontendPayload<MarketMapData>(path);
  } catch (error) {
    if (error instanceof FrontendApiError && error.status === 404) {
      return buildMarketMapFallback();
    }
    throw error;
  }
}

export function getRecommendations() {
  return fetchFrontendPayload<RecommendationListData>("/api/recommendations");
}

export function getRecommendationDetail(recommendationId: string) {
  return fetchFrontendPayload<RecommendationDetailData>(`/api/recommendations/${encodeURIComponent(recommendationId)}`);
}

export function getThesisDetail(thesisId: string, options: { signal?: AbortSignal } = {}) {
  return fetchFrontendPayload<ThesisDetailData>(`/api/theses/${encodeURIComponent(thesisId)}`, options);
}

export function getPortfolioCoverage(asOfDate = currentIsoDate()) {
  const query = new URLSearchParams({ asOfDate });
  return fetchFrontendPayload<PortfolioCoverageData>(
    `/api/portfolio/Long%20Term%20Paper/coverage?${query.toString()}`,
  );
}

export function getAiEvidenceDetail(evidenceId: string) {
  return fetchFrontendPayload<AiEvidenceDetailData>(`/api/ai-evidence/${evidenceId}`);
}

export function getSourceDocumentDetail(documentId: string) {
  return fetchFrontendPayload<SourceDocumentDetailData>(`/api/source-documents/${documentId}`);
}

export function getEvents({
  asOfDate = currentIsoDate(),
  eventType = "all",
  evidenceType = "all",
  limit = 20,
}: {
  asOfDate?: string;
  eventType?: string;
  evidenceType?: string;
  limit?: number;
} = {}) {
  const params = new URLSearchParams({
    asOfDate,
    eventType,
    evidenceType,
    limit: String(limit),
  });
  return fetchFrontendPayload<EventListData>(`/api/events?${params.toString()}`);
}

export function getThemeDetail(themeKey: string) {
  const query = new URLSearchParams({ asOfDate: currentIsoDate() });
  return fetchFrontendPayload<ThemeDetailData>(`/api/themes/${themeKey}?${query.toString()}`);
}

export function getPerformanceOutcomes() {
  const query = new URLSearchParams({ measurementEndDate: currentIsoDate() });
  return fetchFrontendPayload<PerformanceOutcomesData>(
    `/api/performance/Long%20Term%20Paper/outcomes?${query.toString()}`,
  );
}

function currentIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function buildMarketMapFallback(): ApiResponse<MarketMapData> {
  const asOfDate = currentIsoDate();
  return {
    contract_version: "frontend-api-v0.1",
    generated_at: new Date().toISOString(),
    data: {
      as_of_date: asOfDate,
      snapshot_as_of_date: null,
      summary: {
        status: "missing",
        indicator_count: 0,
        fresh_indicator_count: 0,
        stale_indicator_count: 0,
        missing_indicator_count: 0,
        shock_indicator_count: 0,
        regime_count: 0,
        active_regime_count: 0,
        watch_regime_count: 0,
        conflict_regime_count: 0,
        news_link_count: 0,
        correlation_count: 0,
        strong_correlation_count: 0,
        moderate_correlation_count: 0,
        correlation_as_of_date: null,
        latest_observation_date: null,
        next_action: "market-indicator-daily, cross-asset-regime-daily, correlation-analysis-run 실행 후 시장 지도를 다시 확인한다.",
        recommendation_scoring_mutated: false,
        automatic_weight_change_allowed: false,
        broker_submit_allowed: false,
        order_boundary: "read_only_no_order",
      },
      groups: [],
      regimes: [],
      news_links: [],
      correlations: [],
      quality_flags: [],
      guardrails: [
        "시장 지도는 추천 점수나 주문을 직접 변경하지 않는다.",
        "stale 지표는 추정값으로 채우지 않고 신뢰도를 낮춰 표시한다.",
        "상관관계는 같이 움직인 정도만 보여주며 원인을 단정하지 않는다.",
      ],
    },
    links: {
      data_health: "/api/data-health",
      cycle_map: `/api/cycle-map?asOfDate=${asOfDate}`,
    },
  };
}

function buildAiAgentRegistryFallback(): ApiResponse<AiAgentRegistryData> {
  const now = new Date().toISOString();
  const codexOauthOperator: CodexOauthOperatorStatus = {
    status: "unknown",
    label: "미확인",
    summary: "AI 운영 상태 endpoint가 아직 연결되지 않았다.",
    auth_url: "",
    user_code: "",
    expires_at: "",
    device_auth_pid: null,
    last_checked_at: "",
    last_event_type: "",
    last_smoke_status: "",
    last_smoke_at: "",
    last_error_code: "",
    last_error_summary: "",
    next_action: "실제 API 연결 뒤 Codex OAuth 상태를 확인한다.",
    login_probe_status: "not_checked",
    login_probe_message: "",
    status_path: "",
    admin_action_required: true,
    read_only: true,
    broker_submit_allowed: false,
    automatic_order_allowed: false,
    order_boundary: "read_only_no_order",
  };
  const openaiProviderHealth = {
    status: "unknown",
    label: "미확인",
    balance_known: false,
    balance_check_method: "미연결",
    remaining_balance_usd: null,
    api_key_configured: false,
    admin_api_key_configured: false,
    last_checked_at: "",
    next_retry_at: "",
    fallback_provider: "codex_oauth",
    local_fallback_provider: "local_rules",
    message: "OpenAI 비용과 잔액 상태를 이 화면에서 아직 조회하지 못했다.",
    cost_status: {
      report_name: "openai-cost-status",
      status: "미확인",
      cost_known: false,
      admin_api_key_configured: false,
      lookback_days: 7,
      total_cost_usd: null,
      latest_day_cost_usd: null,
      currency: "USD",
      period_start: "",
      period_end: "",
      last_checked_at: "",
      error_code: "",
      message: "비용 조회 화면이 아직 연결되지 않았다.",
      billing_overview_url: "https://platform.openai.com/settings/organization/billing/overview",
      secret_free: true,
    },
  };
  const baseAgent = {
    prompt_version: "미연결",
    prompt_cache_key: "미연결",
    output_schema_name: "미연결",
    model_policy: {
      primary_provider: "codex_oauth",
      primary_model: "운영 설정값",
      fallback_provider: "local_rules",
      fallback_model: "규칙 기반",
      local_fallback_provider: "local_rules",
      model_tier: "balanced",
      reasoning_effort: "medium",
      max_input_chars: 0,
      max_requests_per_run: 0,
      daily_usd_cap: "0",
    },
    safety_boundary: {
      can_write_canonical: false,
      can_trigger_order: false,
      requires_approval_for_side_effects: true,
      order_boundary: "read_only_no_order",
    },
    runtime_status: {
      status: "unknown",
      last_run_status: "미연결",
      last_run_at: "",
      latest_provider: "",
      latest_model: "",
      latest_error_code: "",
    },
  };

  return {
    contract_version: "frontend-api-v0.1",
    generated_at: now,
    data: {
      status: "api_not_connected",
      report_name: "ai-agent-registry-fallback",
      agent_count: 3,
      required_agent_count: 3,
      missing_required_agents: [],
      primary_providers: ["codex_oauth"],
      fallback_providers: ["local_rules"],
      local_fallback_providers: ["local_rules"],
      blocked_order_agent_count: 3,
      runtime_policy: {
        model_editing_enabled: false,
        live_request_invocation_enabled: false,
        batch_invocation_only: true,
        canonical_write_enabled: false,
        broker_submit_allowed: false,
        automatic_order_allowed: false,
        order_boundary: "read_only_no_order",
        primary_api_key_configured: false,
        primary_provider_status: "미확인",
        primary_provider_fallback_reason: "AI 운영 registry endpoint가 연결되지 않았다.",
        openai_billing_status: "unknown",
        openai_api_disabled: true,
        openai_provider_health: openaiProviderHealth,
        codex_oauth_status: "unknown",
        codex_oauth_operator: codexOauthOperator,
        configuration_source: "화면 기본값",
        next_action: "FastAPI live API의 AI 에이전트 화면 연결 상태를 확인한다.",
      },
      agents: [
        {
          ...baseAgent,
          agent_key: "news_event_analyst",
          display_name: "뉴스 이벤트 분석 에이전트",
          agent_role: "뉴스를 거시·테마·종목 근거로 구조화한다.",
          owner_domain: "news",
          business_goal: "원천 뉴스, 한국어 번역, 영향 방향, 불확실성을 투자 근거 후보로 정리한다.",
          default_task_name: "news-rss-ai-extract-run",
        },
        {
          ...baseAgent,
          agent_key: "cycle_research_analyst",
          display_name: "사이클 리서치 에이전트",
          agent_role: "거시·섹터·테마·종목 사이클을 연결한다.",
          owner_domain: "cycle",
          business_goal: "뉴스와 시장 지표를 사이클 지도와 추천 근거 맥락으로 요약한다.",
          default_task_name: "cycle-community-ai-summary-run",
        },
        {
          ...baseAgent,
          agent_key: "equity_research_analyst",
          display_name: "기업 분석 에이전트",
          agent_role: "재무·밸류에이션·리스크를 구조화한다.",
          owner_domain: "equity_research",
          business_goal: "기업 리서치 결과물을 만들되 추천 점수와 주문을 직접 바꾸지 않는다.",
          default_task_name: "equity-research-reporting-run",
        },
      ],
    },
    links: {
      data_health: "/api/data-health",
      codex_oauth_status: "/api/admin/ai-agents",
    },
  };
}

function buildCycleMapFallback(): ApiResponse<CycleMapData> {
  const asOfDate = currentIsoDate();
  return {
    contract_version: "frontend-api-v0.1",
    generated_at: new Date().toISOString(),
    data: {
      as_of_date: asOfDate,
      summary: {
        node_count: 2,
        macro_count: 1,
        domain_count: 0,
        sector_count: 0,
        theme_count: 1,
        instrument_count: 0,
        conflict_node_count: 0,
        direct_event_count: 1,
        propagated_impact_count: 0,
        recommendation_count: 0,
        thesis_count: 0,
        hot_node_code: "ANNUAL_REPORTING",
      },
      nodes: [
        {
          node_id: "classification-node-macro-market-quality",
          node_code: "MACRO_GROWTH",
          node_name: "Macro growth",
          node_type: "macro",
          description: "대표 거시 흐름",
          cycle_level: "macro",
          cycle_state: "watch",
          cycle_score: 0.5,
          trend_score: null,
          breadth_score: null,
          event_heat_score: 0.4,
          liquidity_score: null,
          valuation_pressure: null,
          parent_alignment_score: null,
          conflict_flags: [],
          evidence_event_ids: ["event-aapl-10k"],
          summary_text_ko: "최신 흐름 지도 데이터가 아직 충분히 연결되지 않아 대표 거시 흐름만 표시한다.",
          top_symbols: ["AAPL"],
          recent_event_titles: ["AAPL 2024 10-K annual reporting event"],
          parent_codes: [],
          child_codes: ["ANNUAL_REPORTING"],
          counts: {
            parent_edge_count: 0,
            child_edge_count: 1,
            direct_event_count: 1,
            propagated_impact_count: 0,
            exposed_instrument_count: 1,
            ai_artifact_count: 0,
            recommendation_count: 0,
            thesis_count: 0,
          },
          summary_as_of_date: asOfDate,
          source_run_id: null,
          updated_at: new Date().toISOString(),
        },
        {
          node_id: "classification-node-annual-reporting",
          node_code: "ANNUAL_REPORTING",
          node_name: "Annual reporting quality",
          node_type: "theme",
          description: "대표 테마 흐름",
          cycle_level: "theme",
          cycle_state: "constructive",
          cycle_score: 0.62,
          trend_score: null,
          breadth_score: null,
          event_heat_score: 0.7,
          liquidity_score: null,
          valuation_pressure: null,
          parent_alignment_score: null,
          conflict_flags: [],
          evidence_event_ids: ["event-aapl-10k"],
          summary_text_ko: "연간 공시 품질 흐름을 대표 흐름으로 표시한다.",
          top_symbols: ["AAPL"],
          recent_event_titles: ["AAPL 2024 10-K annual reporting event"],
          parent_codes: ["MACRO_GROWTH"],
          child_codes: [],
          counts: {
            parent_edge_count: 1,
            child_edge_count: 0,
            direct_event_count: 1,
            propagated_impact_count: 0,
            exposed_instrument_count: 1,
            ai_artifact_count: 1,
            recommendation_count: 1,
            thesis_count: 1,
          },
          summary_as_of_date: asOfDate,
          source_run_id: null,
          updated_at: new Date().toISOString(),
        },
      ],
      edges: [
        {
          parent_code: "MACRO_GROWTH",
          parent_name: "Macro growth",
          child_code: "ANNUAL_REPORTING",
          child_name: "Annual reporting quality",
          relation_type: "influences",
          weight: 0.45,
        },
      ],
    },
    links: {
      events: "/api/events?asOfDate=2024-11-01",
      recommendations: "/api/recommendations",
    },
  };
}

function buildAiEvidenceNeighborhoodFallback(symbol: string): ApiResponse<AiEvidenceNeighborhoodData> {
  const asOfDate = currentIsoDate();
  return {
    contract_version: "frontend-api-v0.1",
    generated_at: new Date().toISOString(),
    data: {
      symbol,
      as_of_date: asOfDate,
      retrieval_boundary: {
        mode: "read_only_fallback",
        retrieval_backend: "postgres_sql_graph_neighborhood",
        vector_backend: "disabled",
        graph_backend: "postgres_ontology_lite",
        live_llm_call_enabled: false,
        token_budget: 0,
        cost_estimate_usd: 0,
      },
      instrument: {
        symbol,
        instrument_id: `instrument-${symbol.toLowerCase()}`,
        name: symbol,
        market_code: "US",
        found: true,
      },
      summary: {
        theme_count: 0,
        theme_edge_count: 0,
        event_count: 0,
        story_group_count: 0,
        ai_artifact_count: 0,
        evidence_chunk_count: 0,
        embedded_chunk_count: 0,
        thesis_count: 0,
        recommendation_count: 0,
        position_count: 0,
      },
      themes: [],
      theme_edges: [],
      events: [],
      story_groups: [],
      ai_artifacts: [],
      evidence_chunks: [],
      theses: [],
      recommendations: [],
      positions: [],
      internal_rag_context: {
        status: "not_available",
        symbol,
        as_of_date: asOfDate,
        retrieval_policy: {
          mode: "read_only_fallback",
          retrieval_backend: "postgres_sql_graph_neighborhood",
          canonical_store: "postgres",
          vector_backend: "disabled",
          graph_backend: "postgres_ontology_lite",
          external_rag_service: "none",
          external_vector_db: "none",
          external_graph_db: "none",
          live_llm_call_enabled: false,
          write_enabled: false,
          broker_submit_allowed: false,
          order_boundary: "read_only_no_order",
        },
        context_inventory: {
          theme_count: 0,
          theme_edge_count: 0,
          event_count: 0,
          story_group_count: 0,
          ai_artifact_count: 0,
          evidence_chunk_count: 0,
          translated_event_count: 0,
          thesis_count: 0,
          recommendation_count: 0,
          position_count: 0,
          estimated_prompt_chars: 0,
        },
        quality_gates: [
          {
            gate: "stored_relationship_context",
            status: "warning",
            message_ko: "이 종목의 저장 근거 관계망이 아직 충분히 연결되지 않아 빈 관계망으로 표시한다.",
          },
        ],
        sections: [],
        evidence_items: [],
        prompt_context: {
          language: "ko",
          purpose: "read_only_context_preview",
          instruction: "저장된 뉴스·공시·추천 관계가 연결되면 이 문맥이 채워진다.",
          context_char_budget: 0,
          context_text: "",
        },
        guardrails: [
          "이 화면은 실시간 AI 호출을 하지 않는다.",
          "이 데이터는 주문이나 추천 산식 변경에 쓰지 않는다.",
        ],
      },
      guardrails: [
        "이 화면은 저장된 근거 관계만 읽는다.",
        "관계망 데이터가 연결되기 전까지 추천 점수나 주문에는 쓰지 않는다.",
      ],
    },
    links: {
      stock: `/api/stocks/${encodeURIComponent(symbol)}`,
    },
  };
}
