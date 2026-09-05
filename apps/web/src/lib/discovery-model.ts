/** Read-only projections. No source defaults may turn absence into price, readiness or alpha. */
import { count, fraction, isoDate, record, text } from "./research-home-model";
export { count, fraction, isoDate };
export type Obj = Record<string, unknown>;
export type DiscoveryKind = "stocks" | "cycles" | "market";
export type DiscoveryData = { kind: DiscoveryKind; asOfDate: string | null; partial: boolean; raw: Obj; rows: Obj[] };
export type ObservationState = "matching" | "historical" | "future" | "unknown";
export const finite = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;
export const label = (v: unknown, fallback = "미확인") => text(v, fallback);
export const object = record;
export function objectRows(value: unknown, required = false): Obj[] {
  if (value == null && !required) return [];
  if (!Array.isArray(value) || value.some(v => v === null || typeof v !== "object" || Array.isArray(v))) throw new Error("invalid discovery rows");
  return value;
}
function unique(rows: Obj[], field: string): void {
  const ids = rows.map(row => label(row[field], ""));
  if (ids.some(id => !id) || new Set(ids).size !== ids.length) throw new Error("invalid discovery identity");
}
export function parseDiscovery(kind: DiscoveryKind, payload: unknown): DiscoveryData {
  const envelope = record(payload), raw = record(envelope.data);
  const field = kind === "stocks" ? "stocks" : kind === "cycles" ? "cycle_states" : "groups";
  const rows = objectRows(raw[field], true);
  unique(rows, kind === "stocks" ? "instrument_id" : kind === "cycles" ? "theme_key" : "group_code");
  if (kind === "stocks" && rows.some(row => !label(row.symbol, ""))) throw new Error("missing stock symbol");
  if (kind === "market") {
    for (const group of rows) unique(objectRows(group.indicators, true), "indicator_code");
    for (const field of ["regimes", "correlations", "news_links", "quality_flags"]) objectRows(raw[field]);
  }
  return { kind, rows, raw, partial: record(envelope.pagination).has_more === true,
    asOfDate: isoDate(kind === "market" ? raw.snapshot_as_of_date : raw.as_of_date) };
}
export function observationState(value: unknown, reference: unknown): ObservationState {
  const date = isoDate(value), at = isoDate(reference);
  if (!date || !at) return "unknown";
  return date > at ? "future" : date < at ? "historical" : "matching";
}
export function dateLabel(value: unknown, reference: unknown): string {
  const state = observationState(value, reference);
  return state === "unknown" ? (isoDate(value) ? `${isoDate(value)} · 비교 기준 미확인` : "기준일 미확인") : `${isoDate(value)} · ${state === "future" ? "미래 기준일 · 확인 필요" : state === "historical" ? "과거 기준" : "조회 기준일과 일치"}`;
}
export function priceAttention(row: Obj, reference: unknown): boolean {
  const p = record(row.latest_price);
  return finite(p.close) === null || Number(p.close) <= 0 || observationState(p.trade_date, reference) !== "matching";
}
export function linked(row: Obj, kind: "recommendation" | "position"): boolean {
  const value = record(row[kind]);
  return kind === "recommendation" ? !!label(value.recommendation_id, "") : !!label(value.portfolio_name, "");
}
export function currency(value: unknown, code: unknown): string {
  const n = finite(value), c = label(code, "");
  if (n === null || n <= 0) return "가격 미확인";
  if (!/^[A-Z]{3}$/.test(c)) return `${n.toLocaleString("ko-KR")} · 통화 미확인`;
  return new Intl.NumberFormat("ko-KR", { style: "currency", currency: c, maximumFractionDigits: 2 }).format(n);
}
export function numberLabel(value: unknown, digits = 2): string {
  const n = finite(value); return n === null ? "미측정" : n.toLocaleString("ko-KR", { maximumFractionDigits: digits });
}
export function ratioLabel(value: unknown): string {
  const n = fraction(value); return n === null ? "미측정" : `${(n * 100).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}%`;
}
export function validState(value: unknown): string | null {
  const state = label(value, "");
  return !state || ["unknown", "missing", "unavailable", "not_available"].includes(state.toLowerCase()) ? null : state;
}
export function changedCycle(row: Obj): boolean {
  const before = validState(row.previous_state), after = validState(row.state);
  return !!before && !!after && before !== after;
}
export const FEATURE_KEYS = ["event_intensity", "price_momentum", "fundamental_quality"] as const;
export function cycleGap(row: Obj): boolean {
  return FEATURE_KEYS.some(key => fraction(record(row.features)[key]) === null);
}
export function cycleSummary(rows: readonly Obj[]) {
  const counts = rows.map(row => count(row.instrument_count));
  const measured = rows.map(row => fraction(row.confidence)).filter((v): v is number => v !== null);
  return {
    changed: rows.filter(changedCycle).length,
    historyUnknown: rows.filter(row => !validState(row.previous_state) || !validState(row.state)).length,
    gaps: rows.filter(cycleGap).length,
    memberships: rows.length && counts.every(v => v !== null) ? counts.reduce<number>((sum, v) => sum + (v ?? 0), 0) : null,
    confidence: measured.length ? measured.reduce((a, b) => a + b, 0) / measured.length : null,
    confidenceCount: measured.length,
  };
}
export function flattenMarket(groups: readonly Obj[]): Obj[] {
  return groups.flatMap(group => objectRows(group.indicators).map(row => ({ ...row, group_code: group.group_code, group_name: group.group_name })));
}
export function marketAttention(row: Obj, reference: unknown): boolean {
  return label(row.freshness_status) !== "fresh" || finite(row.latest_value) === null || !isoDate(row.latest_observation_date)
    || observationState(row.latest_observation_date, reference) === "future";
}
export function filterDiscovery(rows: readonly Obj[], kind: DiscoveryKind, query: string, scope: string, group: string, reference: unknown): Obj[] {
  const needle = query.trim().toLocaleLowerCase();
  return rows.filter(row => {
    const haystack = [row.symbol, row.name, row.market_code, row.theme_key, row.theme_name, row.indicator_code, row.display_name, row.group_name,
      ...(Array.isArray(row.top_symbols) ? row.top_symbols : [])].map(v => label(v, "")).join(" ").toLocaleLowerCase();
    if (!haystack.includes(needle) || (group && row.group_code !== group)) return false;
    if (scope === "all") return true;
    if (kind === "stocks") return scope === "recommended" ? linked(row, "recommendation") : scope === "held" ? linked(row, "position") : priceAttention(row, reference);
    if (kind === "cycles") return scope === "changed" ? changedCycle(row) : scope === "history" ? !validState(row.previous_state) || !validState(row.state) : cycleGap(row);
    return marketAttention(row, reference);
  });
}
export function safeSource(value: unknown): string | null {
  if (typeof value !== "string") return null;
  try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null; }
  catch { return null; }
}
export function scopesFor(kind: DiscoveryKind): readonly { key: string; name: string }[] {
  return kind === "stocks" ? [{ key: "all", name: "전체 종목" }, { key: "recommended", name: "추천 연결" }, { key: "held", name: "보유 연결" }, { key: "attention", name: "가격 확인" }]
    : kind === "cycles" ? [{ key: "all", name: "전체 테마" }, { key: "changed", name: "상태 전환" }, { key: "history", name: "이전 상태 미확인" }, { key: "gaps", name: "특징 미측정" }]
    : [{ key: "all", name: "전체 지표" }, { key: "attention", name: "원천 확인 필요" }];
}
