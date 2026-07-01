import { ensureArray, ensureRecord, isRecord, type MutableRecord, withDefault } from "./frontend-normalizer-utils";

function currentIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export function normalizeMarketMapPayload(data: MutableRecord) {
  withDefault(data, "as_of_date", currentIsoDate());
  withDefault(data, "snapshot_as_of_date", null);
  const summary = ensureRecord(data, "summary");
  for (const key of [
    "indicator_count",
    "fresh_indicator_count",
    "stale_indicator_count",
    "missing_indicator_count",
    "shock_indicator_count",
    "regime_count",
    "active_regime_count",
    "watch_regime_count",
    "conflict_regime_count",
    "news_link_count",
    "correlation_count",
    "strong_correlation_count",
    "moderate_correlation_count",
  ]) {
    withDefault(summary, key, 0);
  }
  withDefault(summary, "status", "missing");
  withDefault(summary, "correlation_as_of_date", null);
  withDefault(summary, "latest_observation_date", null);
  withDefault(summary, "next_action", "시장 지표 수집과 상관관계 분석을 실행한 뒤 다시 확인한다.");
  withDefault(summary, "recommendation_scoring_mutated", false);
  withDefault(summary, "automatic_weight_change_allowed", false);
  withDefault(summary, "broker_submit_allowed", false);
  withDefault(summary, "order_boundary", "read_only_no_order");

  for (const rawGroup of ensureArray(data, "groups")) {
    if (!isRecord(rawGroup)) {
      continue;
    }
    withDefault(rawGroup, "group_code", "UNKNOWN");
    withDefault(rawGroup, "group_name", "시장 지표");
    withDefault(rawGroup, "indicator_count", 0);
    withDefault(rawGroup, "fresh_count", 0);
    withDefault(rawGroup, "stale_count", 0);
    withDefault(rawGroup, "missing_count", 0);
    withDefault(rawGroup, "shock_count", 0);
    withDefault(rawGroup, "latest_observation_date", null);
    withDefault(rawGroup, "strongest_indicator_code", null);
    ensureArray(rawGroup, "indicators");
  }

  for (const rawRegime of ensureArray(data, "regimes")) {
    if (!isRecord(rawRegime)) {
      continue;
    }
    withDefault(rawRegime, "driver_indicator_codes", []);
    withDefault(rawRegime, "conflict_flags", []);
    withDefault(rawRegime, "summary_ko", "시장 체제 설명이 아직 충분히 연결되지 않았다.");
  }

  for (const rawLink of ensureArray(data, "news_links")) {
    if (!isRecord(rawLink)) {
      continue;
    }
    withDefault(rawLink, "title_ko", "제목 미수집");
    withDefault(rawLink, "source_name", "");
    withDefault(rawLink, "source_url", "");
    withDefault(rawLink, "rationale", "");
    withDefault(rawLink, "relationship", "temporal_evidence");
    withDefault(rawLink, "confidence", 0);
  }

  ensureArray(data, "correlations");
  ensureArray(data, "quality_flags");
  ensureArray(data, "guardrails");
}
