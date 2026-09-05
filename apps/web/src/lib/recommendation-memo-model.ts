/** Read-only presentation: never invent a claim, valuation, review date or permission. */
import type { RecommendationDetailData, ThesisDetailData } from "./types";
import { count, isoDate, record, rows, text } from "./research-home-model";

export type MemoThesisResult =
  | { status: "available"; data: ThesisDetailData }
  | { status: "not_linked" | "unavailable" | "timeout" | "mismatch"; data: null };
export const NO_LINKED_THESIS: MemoThesisResult = { status: "not_linked", data: null };
export type MemoTone = "ready" | "watch" | "blocked";

export function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
export function memoPercent(value: unknown): string {
  const number = finiteNumber(value);
  return number === null ? "미확인" : new Intl.NumberFormat("ko-KR", { style: "percent", maximumFractionDigits: 2 }).format(number);
}
export function memoCurrency(value: unknown, currency: unknown): string {
  const number = finiteNumber(value);
  if (number === null) return "미측정";
  if (typeof currency !== "string" || !/^[A-Z]{3}$/.test(currency)) return "통화 미확인";
  try { return new Intl.NumberFormat("ko-KR", { style: "currency", currency, maximumFractionDigits: currency === "KRW" ? 0 : 2 }).format(number); }
  catch { return "통화 미확인"; }
}
export function memoDate(value: unknown): string | null {
  if (typeof value !== "string") return null;
  if (isoDate(value)) return value;
  return /^\d{4}-\d{2}-\d{2}T/.test(value) && Number.isFinite(Date.parse(value)) ? isoDate(value.slice(0, 10)) : null;
}
export function memoPositionLabel(status: unknown): string {
  return status === "held" ? "보유 중" : status === "not_held" ? "미보유" : "보유 상태 미확인";
}
export function memoPositionSummary(position: unknown): string {
  const p = record(position);
  if (p.status === "not_held") return "확인된 미보유 상태입니다.";
  if (p.status !== "held") return "보유 원장을 확인하지 못했습니다. 미보유로 간주하지 않습니다.";
  return `현재 비중 ${memoPercent(p.weight)} · 평단가 ${memoCurrency(p.average_cost, p.currency_code)}`;
}
export function thesisMatchesRecommendation(data: RecommendationDetailData, value: unknown): value is ThesisDetailData {
  const thesis = record(value);
  return Boolean(text(data.linked_thesis_id, "") && thesis.thesis_id === data.linked_thesis_id
    && text(data.symbol, "") && thesis.symbol === data.symbol
    && text(data.instrument_id, "") && thesis.instrument_id === data.instrument_id);
}
export function memoEvidenceAssessment(value: unknown): { label: string; detail: string; tone: MemoTone } {
  const audit = record(value);
  const expected = count(audit.expected_layer_count), available = count(audit.available_layer_count);
  const missing = count(audit.missing_layer_count), pending = count(audit.pending_layer_count), blocked = count(audit.blocked_layer_count);
  if (record(audit.source_blocker).blocked === true || (blocked !== null && blocked > 0) || audit.status === "source_blocked") {
    return { label: "원천 근거 제한", detail: text(record(audit.source_blocker).summary, "제한된 근거를 투자 판단에 사용하지 마세요."), tone: "blocked" };
  }
  if (expected === null || expected === 0 || available === null || available > expected
    || missing === null || pending === null || blocked === null
    || !["complete", "available", "passed", "review_ready", "paper_validation_pending"].includes(text(audit.status, ""))) {
    return { label: "근거 상태 미확인", detail: "기대 근거 수와 감사 상태가 확인되지 않았습니다. 0/0은 충족이 아닙니다.", tone: "watch" };
  }
  const complete = available === expected && missing === 0 && pending === 0 && count(audit.partial_layer_count) === 0;
  return { label: `${available}/${expected}개 근거 연결`, detail: `누락 ${missing}개 · 대기 ${pending}개. 연결 수는 투자 성공 확률이 아닙니다.`, tone: complete ? "ready" : "watch" };
}
function strings(value: unknown): string[] {
  return Array.isArray(value) ? [...new Set(value.filter((v): v is string => typeof v === "string" && Boolean(v.trim())).map(v => v.trim()))] : [];
}
function safeSourceId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]*$/.test(value);
}

export function buildRecommendationMemo(data: RecommendationDetailData, linked: MemoThesisResult = NO_LINKED_THESIS) {
  const matched = linked.status === "available" && thesisMatchesRecommendation(data, linked.data);
  const thesis = record(matched ? linked.data : null);
  const lifecycle = record(thesis.lifecycle);
  const buyCase = record(lifecycle.buy_case);
  const review = record(thesis.latest_review);
  const fund = record(data.fund_instrument_analysis);
  const isFund = Boolean(data.fund_instrument_analysis) || data.professional_evidence_audit?.product_type === "fund_or_etf";
  // Never reuse an accidentally attached company analysis as an ETF valuation.
  const research = isFund ? {} : record(data.equity_research);
  const researchDate = memoDate(research.as_of_date);
  const reviewDate = memoDate(review.reviewed_at);
  const thesisNotice = linked.status === "available" && !matched ? "mismatch" : linked.status;
  const notice = {
    available: "연결된 투자 논리를 확인했습니다.",
    not_linked: "연결된 투자 논리가 없습니다. 아래 기업·상품 분석을 독립된 근거로 확인하세요.",
    unavailable: "연결된 투자 논리를 불러오지 못했습니다. 다른 분석 자료는 계속 표시합니다.",
    timeout: "투자 논리 응답이 지연되어 해당 자료만 생략했습니다.",
    mismatch: "투자 논리의 식별자·종목 연결이 달라 해당 자료를 표시하지 않습니다.",
  }[thesisNotice];
  const claimSource = matched ? `저장된 투자 논리 · 최근 검토 ${reviewDate ?? "미기록"}`
    : isFund ? `ETF·펀드 분석 · ${memoDate(fund.source_as_of_date) ?? "기준일 미확인"}`
      : `기업 리서치 해석 · ${researchDate ?? "기준일 미확인"}`;
  const summary = matched ? text(thesis.summary, text(buyCase.summary, "핵심 투자 논리가 기록되지 않았습니다."))
    : isFund ? text(fund.summary, "ETF 투자 논리가 기록되지 않았습니다.")
      : text(research.korean_summary, "핵심 투자 논리가 기록되지 않았습니다.");
  const claims = matched ? strings(thesis.core_claims).length ? strings(thesis.core_claims) : strings(buyCase.core_claims) : strings(research.key_points);
  const catalystSource = matched && strings(lifecycle.catalysts).length ? claimSource : isFund ? claimSource : `기업 리서치 해석 · ${researchDate ?? "기준일 미확인"}`;
  const riskSource = matched && strings(lifecycle.risks).length ? claimSource : isFund ? claimSource : `기업 리서치 해석 · ${researchDate ?? "기준일 미확인"}`;
  const catalysts = matched && strings(lifecycle.catalysts).length ? strings(lifecycle.catalysts) : strings(research.catalysts);
  const risks = matched && strings(lifecycle.risks).length ? strings(lifecycle.risks) : isFund ? strings(fund.limitations) : strings(research.risks);
  const thesisConditions = rows(thesis.invalidation_conditions).length ? rows(thesis.invalidation_conditions) : rows(lifecycle.invalidation_conditions);
  const conditions = thesisConditions.length ? thesisConditions.filter(c => text(c.condition, "")).map(c => ({ condition: text(c.condition), status: text(c.current_status, "미확인") }))
    : strings(research.invalidation_conditions).map(condition => ({ condition, status: "미확인" }));
  const valuation = record(data.valuation_target_range);
  const validValuation = valuation.status === "available" && finiteNumber(valuation.target_base) !== null && (valuation.target_base as number) > 0;
  const methods = rows(valuation.methods).map(method => ({
    name: text(method.method_label, text(method.method, "모형명 미확인")),
    date: memoDate(method.as_of_date),
    assumptions: rows(method.assumption_items).map(item => ({ label: text(item.label), value: text(item.value, "미기록"), interpretation: text(item.interpretation, "") })),
  }));
  return {
    isFund, summary, claims, claimSource, notice,
    catalysts, catalystSource, risks, riskSource, conditions,
    conditionSource: thesisConditions.length || isFund ? claimSource : `기업 리서치 해석 · ${researchDate ?? "기준일 미확인"}`,
    evidence: memoEvidenceAssessment(data.professional_source_guardrail?.blocked === true || data.professional_decision_waterfall?.status === "source_data_blocked"
      ? { ...record(data.professional_evidence_audit), status: "source_blocked" } : data.professional_evidence_audit),
    positionLabel: memoPositionLabel(data.position_context?.status), positionSummary: memoPositionSummary(data.position_context),
    analysisDate: memoDate(data.as_of_date), researchDate,
    valuation: {
      referencePrice: memoCurrency(valuation.base_price, valuation.currency_code),
      target: validValuation ? memoCurrency(valuation.target_base, valuation.currency_code) : "미측정",
      low: validValuation ? memoCurrency(valuation.target_low, valuation.currency_code) : "미측정",
      high: validValuation ? memoCurrency(valuation.target_high, valuation.currency_code) : "미측정",
      date: memoDate(valuation.valuation_as_of_date), methods,
    },
    fund: { count: count(fund.holding_count), coverage: memoPercent(fund.holdings_coverage_weight),
      expense: ["available", "collected"].includes(text(record(fund.expense_ratio).status, "")) ? memoPercent(record(fund.expense_ratio).value) : "미확인",
      expenseDate: memoDate(record(fund.expense_ratio).source_as_of_date), date: memoDate(fund.source_as_of_date), benchmark: text(fund.benchmark_code, "미확인") },
    reviewedAt: reviewDate, nextReview: memoDate(review.next_review_date), reviewSummary: text(review.summary, "검토 기록이 없습니다."),
    thesisHref: matched && safeSourceId(thesis.thesis_id) ? `/theses/${encodeURIComponent(thesis.thesis_id)}` : null,
    sources: strings(research.source_document_ids).filter(safeSourceId).map(id => ({ id, href: `/source-documents/${encodeURIComponent(id)}` })),
  };
}
