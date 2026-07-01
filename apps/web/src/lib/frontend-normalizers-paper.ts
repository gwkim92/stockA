import { ensureRecord, type MutableRecord, withDefault } from "./frontend-normalizer-utils";

export function normalizePaperTradingPreviewPayload(data: MutableRecord) {
  const summary = ensureRecord(data, "quality_summary");
  withDefault(summary, "recommendation_count", 0);
  withDefault(summary, "measured_recommendation_count", 0);
  withDefault(summary, "unmeasured_recommendation_count", 0);
  withDefault(summary, "hit_rate", null);
  withDefault(summary, "average_alpha", null);
  withDefault(summary, "position_recommendation_conflict_count", 0);
  withDefault(summary, "paper_action_count", 0);
  withDefault(summary, "requires_human_approval_count", 0);
  withDefault(data, "execution_boundary", {
    mode: "simulated_paper_validation",
    portfolio_kind: "paper",
    live_account_provider: "tossinvest",
    live_account_used_for_recommendation_scoring: false,
    broker_submit_allowed: false,
    submitted_to_broker: false,
    order_boundary: "read_only_no_order",
  });
  withDefault(data, "paper_actions", []);
  withDefault(data, "guardrails", []);
}
