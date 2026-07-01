import { type MutableRecord, withDefault } from "./frontend-normalizer-utils";

function defaultTossInvestMarketData() {
  return {
    sync: {
      status: "not_configured",
      latest_status: "missing",
      latest_run_id: null,
      finished_at: "",
      provider: "tossinvest",
      sync_mode: "not_available",
      market_code: "",
      requested_symbol_count: 0,
      candle_symbol_count: 0,
      candle_bar_count: 0,
      stock_warning_symbol_count: 0,
      market_microdata_symbol_count: 0,
      unresolved_symbol_count: 0,
      collection_cadence: {},
      credentials_configured: false,
      missing_env_vars: [],
      operator_action: "Toss 시장 데이터 수집 설정과 최신 실행 상태를 확인한다.",
      attention_required: true,
      broker_submit_allowed: false,
      submitted_to_broker: false,
      order_boundary: "read_only_no_order",
      secret_free: true,
    },
    provider_comparison: {
      status: "missing",
      latest_status: "missing",
      latest_run_id: null,
      finished_at: "",
      symbol_count: 0,
      comparison_date: "",
      lookback_days: 5,
      max_diff_bps: "50",
      canonical_promotion_blocked: true,
      attention_required: true,
      broker_submit_allowed: false,
      submitted_to_broker: false,
      secret_free: true,
    },
  };
}

export function normalizeDataHealthPayload(data: MutableRecord) {
  withDefault(data, "tossinvest_market_data", defaultTossInvestMarketData());
}
