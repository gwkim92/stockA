/** Presentation projections only: never rewrite financial source values or permissions. */
import { count, fraction, isoDate, record, text } from "./research-home-model";
import { calculatePortfolioReturnSummary, calculatePositionReturn } from "./presentation/returns";

export const REVIEW_PORTFOLIO = "Long Term Paper";
export type ReviewKind = "portfolio" | "performance";
export type Row = Record<string, unknown>;
export type ReviewReport = { kind: ReviewKind; raw: Row; rows: Row[]; partial: boolean };
export { count, fraction, isoDate, record };
export const words = (value: unknown, fallback = "미확인") => text(value, fallback);
export const number = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;
export const code = (v: unknown): string | null => typeof v === "string" && /^[A-Z]{3}$/.test(v) ? v : null;
export function list(value: unknown): Row[] | null {
  return Array.isArray(value) && value.every(v => v !== null && typeof v === "object" && !Array.isArray(v)) ? value : null;
}
export function parseReviewReport(kind: ReviewKind, payload: unknown): ReviewReport {
  const envelope = record(payload), raw = record(envelope.data);
  if (raw.portfolio_name !== REVIEW_PORTFOLIO) throw new Error("report portfolio mismatch");
  const rows = list(raw[kind === "portfolio" ? "positions" : "outcomes"]);
  if (!rows) throw new Error("missing primary list");
  const idKey = kind === "portfolio" ? "instrument_id" : "outcome_id";
  const ids = rows.map(row => words(row[idKey], ""));
  if (ids.some(id => !id) || new Set(ids).size !== ids.length || rows.some(row => !words(row.symbol, ""))) throw new Error("invalid row identity");
  return { kind, raw, rows, partial: record(envelope.pagination).has_more === true };
}
export function selectedDate(value: unknown, today: string): string | null {
  if (value === undefined) return today;
  const parsed = isoDate(value);
  return parsed && parsed <= today ? parsed : null;
}
export function percent(value: unknown, points = false): string {
  const n = number(value);
  return n === null ? "미측정" : `${n > 0 ? "+" : ""}${(n * 100).toLocaleString("ko-KR", { maximumFractionDigits: 2 })}${points ? "%p" : "%"}`;
}
export function weight(value: unknown): string {
  const n = fraction(value);
  return n === null ? "미확인" : `${(n * 100).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}%`;
}
export function money(value: unknown, currency: unknown): string {
  const n = number(value), c = code(currency);
  if (n === null) return "미측정";
  if (!c) return "통화 미확인";
  return new Intl.NumberFormat("ko-KR", { style: "currency", currency: c, maximumFractionDigits: 2 }).format(n);
}
export function dateContext(observed: unknown, requested: string): string {
  const date = isoDate(observed);
  return !date ? "자료 기준일 미확인" : `${date}${date > requested ? " · 요청 기준일 이후 자료" : date < requested ? " · 요청일보다 이전 자료" : " · 요청 기준일과 일치"}`;
}
export function positiveHorizon(value: unknown): number | null {
  const n = count(value); return n && n > 0 ? n : null;
}
export type Holding = {
  id: string; symbol: string; weight: number | null; currency: string | null;
  market: number | null; cost: number | null; pnl: number | null; returnPct: number | null;
  amountVerified: boolean; thesisId: string | null; thesisState: "linked" | "missing" | "unknown";
  coverage: string; outcome: string; action: string; sizeStatus: string; sizeNote: string;
};
export function holding(row: Row, baseCurrency: unknown): Holding {
  const market = number(row.market_value), cost = number(row.cost_basis);
  const currency = code(row.base_currency);
  // Never substitute native-currency fields for explicitly converted base-currency fields.
  const amountVerified = !!currency && currency === code(baseCurrency) && market !== null && market >= 0 && cost !== null && cost > 0;
  const result = amountVerified ? calculatePositionReturn({ market_value: market, cost_basis: cost, unrealized_pnl: number(row.unrealized_pnl) }) : { unrealizedPnl: null, returnPct: null };
  const thesisId = words(row.active_thesis_id, "") || null;
  return {
    id: words(row.instrument_id), symbol: words(row.symbol), weight: fraction(row.weight), currency, market, cost,
    pnl: result.unrealizedPnl, returnPct: result.returnPct, amountVerified,
    thesisId, thesisState: thesisId ? "linked" : row.active_thesis_id === null || row.active_thesis_id === "" ? "missing" : "unknown",
    coverage: words(row.coverage_status), outcome: words(row.outcome_status), action: words(row.action),
    sizeStatus: words(row.position_size_status), sizeNote: words(row.position_size_note, ""),
  };
}
export function portfolioProjection(report: ReviewReport) {
  const currency = code(report.raw.base_currency);
  const rows = report.rows.map(row => holding(row, currency));
  const eligible = rows.filter(row => row.amountVerified);
  const valuation = calculatePortfolioReturnSummary(eligible.map(row => ({ market_value: row.market, cost_basis: row.cost, unrealized_pnl: row.pnl })));
  return { rows, currency, valuation, excluded: rows.length - eligible.length };
}
export function filterHoldings(rows: readonly Holding[], query: string, scope: string): Holding[] {
  const q = query.trim().toLowerCase();
  return rows.filter(row => `${row.symbol} ${row.action}`.toLowerCase().includes(q)
    && (scope === "thesis" ? row.thesisState !== "linked"
      : scope === "outcome" ? !["measured", "covered"].includes(row.outcome)
      : scope === "valuation" ? !row.amountVerified : true));
}
export type Outcome = {
  id: string; symbol: string; recommendationId: string | null; thesisId: string | null;
  horizon: number | null; action: string; result: string;
  absolute: number | null; benchmark: number | null; alpha: number | null; contribution: number | null;
};
export function outcome(row: Row): Outcome {
  return {
    id: words(row.outcome_id), symbol: words(row.symbol), recommendationId: words(row.recommendation_id, "") || null,
    thesisId: words(row.thesis_id, "") || null, horizon: positiveHorizon(row.horizon_days),
    action: words(row.recommendation), result: words(row.label), absolute: number(row.absolute_return),
    benchmark: number(row.benchmark_return), alpha: number(row.alpha), contribution: number(row.security_contribution_bps),
  };
}
export function filterOutcomes(rows: readonly Outcome[], query: string, scope: string, horizon: string): Outcome[] {
  const q = query.trim().toLowerCase();
  return rows.filter(row => row.symbol.toLowerCase().includes(q)
    && (!horizon || String(row.horizon ?? "unknown") === horizon)
    && (scope === "positive" ? row.alpha !== null && row.alpha > 0
      : scope === "negative" ? row.alpha !== null && row.alpha < 0
      : scope === "unknown" ? row.alpha === null : true));
}
export function performanceHeadline(report: ReviewReport) {
  const summary = record(report.raw.summary), measured = count(summary.measured_recommendation_count);
  const hasMeasurement = measured !== null && measured > 0 && report.rows.length > 0;
  return {
    measured, alpha: hasMeasurement ? number(summary.average_alpha) : null,
    hitRate: hasMeasurement ? fraction(summary.hit_rate) : null,
    excludedWeight: fraction(summary.excluded_weight),
    qualityStatus: words(record(report.raw.quality_evaluation).status),
    sampleStatus: words(record(report.raw.quality_evaluation).sample_size_status),
  };
}
/** Latest recorded history, not a fabricated before/after comparison. */
export function recordedReview(report: ReviewReport) {
  const risk = record(report.raw.risk_budget), history = record(risk.review_decision_history), feedback = record(risk.review_decision_feedback);
  const historyId = words(history.eval_run_id, "");
  const validHistory = !!historyId && history.portfolio_name === report.raw.portfolio_name;
  const decisions = validHistory ? list(history.latest_decisions) : null;
  const feedbackLinked = validHistory && !!words(feedback.eval_run_id, "") && feedback.portfolio_name === report.raw.portfolio_name
    && feedback.source_history_eval_run_id === historyId;
  return { history, decisions, feedback, feedbackLinked, items: feedbackLinked ? list(feedback.latest_items) : null };
}
