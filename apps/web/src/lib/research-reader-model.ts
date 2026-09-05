import type { ValuationTargetRange } from "./types";
/** Stored research presentation only. No financial decisions or inferred translations. */
export type Row = Record<string, unknown>;
export type ReaderKind = "thesis" | "source";
export const object = (v: unknown): Row => v !== null && typeof v === "object" && !Array.isArray(v) ? v as Row : {};
export const text = (v: unknown, fallback = "미확인"): string => typeof v === "string" && v.trim() ? v.trim() : fallback;
export const numeric = (v: unknown): number | null => typeof v === "number" && Number.isFinite(v) ? v : null;
export const count = (v: unknown): number | null => typeof v === "number" && Number.isSafeInteger(v) && v >= 0 ? v : null;
export const strings = (v: unknown): string[] | null => Array.isArray(v) && v.every(x => typeof x === "string") ? v.map(x => x.trim()).filter(Boolean) : null;
export const rows = (v: unknown): Row[] | null => Array.isArray(v) && v.every(x => x !== null && typeof x === "object" && !Array.isArray(x)) ? v as Row[] : null;
export function identifier(value: unknown): string | null {
  if (typeof value !== "string" || !value || value.length > 240 || value !== value.trim() || /[\u0000-\u0020\u007f/\\?#%]/u.test(value) || value === "." || value === "..") return null;
  return value;
}
export function dateOnly(value: unknown): string | null {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value ? value : null;
}
export function recordedDate(value: unknown): string | null {
  if (typeof value !== "string") return null;
  if (dateOnly(value)) return value;
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) || !dateOnly(value.slice(0, 10))) return null;
  return Number.isFinite(Date.parse(value)) ? value : null;
}
export const shortDate = (v: unknown, fallback = "기록 없음") => recordedDate(v)?.slice(0, 10) ?? fallback;
export function nextReview(value: unknown, today: string): string {
  const date = recordedDate(value)?.slice(0, 10);
  return !date ? "미지정" : `${date}${date < today ? " · 예정일 지남" : date === today ? " · 오늘 확인 예정" : ""}`;
}
export type ConditionState = "triggered" | "not_triggered" | "unknown";
export function conditionState(value: unknown): ConditionState {
  return value === "triggered" ? "triggered" : value === "not_triggered" ? "not_triggered" : "unknown";
}
export const conditionLabel = (v: unknown) => conditionState(v) === "triggered" ? "발동 기록" : conditionState(v) === "not_triggered" ? "미발동 기록" : "판정 미확인";
export function safeApiLink(value: unknown, resource: "theses" | "recommendations" | "ai-evidence" | "source-documents"): string | null {
  if (typeof value !== "string") return null;
  const prefix = `/api/${resource}/`;
  if (!value.startsWith(prefix)) return null;
  const encoded = value.slice(prefix.length);
  let id: string;
  try { id = decodeURIComponent(encoded); } catch { return null; }
  return identifier(id) ? `/${resource}/${encodeURIComponent(id)}` : null;
}
export const route = (resource: string, value: unknown) => identifier(value) ? `/${resource}/${encodeURIComponent(value as string)}` : null;
export function knownSymbol(value: unknown): string | null {
  const symbol = text(value, "");
  return symbol && !["UNKNOWN", "UNCLASSIFIED"].includes(symbol.toUpperCase()) && identifier(symbol) ? symbol : null;
}
export type Resolution = "exact" | "alias";
/** Aliases follow the existing backend resolver, not a guessed latest source. */
export function resolveIdentity(kind: ReaderKind, requested: string, data: Row, links: Row): Resolution | null {
  const resolved = identifier(data[kind === "thesis" ? "thesis_id" : "document_id"]);
  if (!resolved || /^(?:thesis|source-document)-unknown$/.test(resolved)) return null;
  if (requested === resolved) return "exact";
  if (kind === "thesis") {
    if (/^\d+$/.test(requested) && resolved === `thesis-${requested}`) return "alias";
    const symbol = requested.match(/^(.+)-bootstrap-v1$/)?.[1];
    return symbol && symbol === data.symbol && /^thesis-\d+$/.test(resolved) ? "alias" : null;
  }
  if (requested.replace(/^source-document-/, "") === resolved.replace(/^source-document-/, "")) return "alias";
  // Numeric document requests may resolve to an external ID; the backend self-link
  // must confirm the actual requested identifier. Show this as alias resolution.
  return /^(?:source-document-)?\d+$/.test(requested)
    && safeApiLink(links.source_document, "source-documents") === route("source-documents", requested) ? "alias" : null;
}
export type Evidence = { id: string; title: string; type: string; observedAt: string | null; href: string | null; action: string };
function evidence(row: Row): Evidence {
  const id = text(row.evidence_id, ""), type = text(row.type, text(row.evidence_type, ""));
  return { id, type, title: text(row.title, "제목 미제공"), observedAt: recordedDate(row.observed_at),
    href: route("ai-evidence", id), action: "연결 해석 보기" };
}
export type Excerpt = { id: string; section: string; locator: string; summary: string };
export type SourceReaderData = {
  id: string; resolution: Resolution; title: string; koreanTitle: string | null; koreanSummary: string | null;
  symbol: string | null; publisher: string; type: string; form: string; periodEnd: string | null;
  filedAt: string | null; fetchedAt: string | null; parser: string; accession: string; checksum: string;
  download: "restricted" | "unavailable" | "unknown"; excerpts: Excerpt[] | null; evidence: Evidence[] | null;
  thesisHref: string | null;
};
export function parseSource(payload: unknown, requested: string): SourceReaderData {
  const envelope = object(payload), data = object(envelope.data), links = object(envelope.links);
  const resolution = resolveIdentity("source", requested, data, links);
  if (!resolution || !text(data.title, "")) throw new Error("source identity or title unavailable");
  const excerpts = rows(data.excerpts);
  if (excerpts && (excerpts.some(row => !identifier(row.chunk_id)) || new Set(excerpts.map(row => row.chunk_id)).size !== excerpts.length)) throw new Error("invalid excerpt identity");
  const retrieval = object(data.retrieval), policy = object(data.access_policy);
  return {
    id: text(data.document_id), resolution, title: text(data.title), koreanTitle: text(data.korean_title, "") || null,
    koreanSummary: text(data.korean_summary, "") || null, symbol: knownSymbol(data.symbol), publisher: text(data.publisher),
    type: text(data.source_type), form: text(data.form_type, ""), periodEnd: dateOnly(data.period_end),
    filedAt: recordedDate(data.filed_at), fetchedAt: recordedDate(retrieval.fetched_at), parser: text(retrieval.parser_version),
    accession: text(data.accession_id), checksum: text(data.checksum),
    // A boolean permission is not a usable URL. Internal storage is never a browser link.
    download: policy.browser_download_enabled === false ? "restricted" : policy.browser_download_enabled === true ? "unavailable" : "unknown",
    excerpts: excerpts?.map(row => ({ id: text(row.chunk_id), section: text(row.section, "구간 미표기"), locator: text(row.locator, "위치 미표기"), summary: text(row.summary, "본문 미제공") })) ?? null,
    evidence: rows(data.linked_evidence)?.map(evidence) ?? null,
    thesisHref: safeApiLink(links.thesis, "theses"),
  };
}
export function filterExcerpts(excerpts: readonly Excerpt[], query: string): Excerpt[] {
  const needle = query.trim().toLocaleLowerCase();
  return excerpts.filter(row => [row.section, row.locator, row.summary].join(" ").toLocaleLowerCase().includes(needle));
}
export type ThesisReaderData = {
  id: string; resolution: Resolution; symbol: string; version: string; status: string; summary: string;
  researchSummary: string | null; researchSource: string; claims: string[] | null; catalysts: string[] | null;
  risks: string[] | null; conditions: { text: string; state: ConditionState }[] | null;
  review: { id: string | null; action: string; risk: string; date: string | null; summary: string | null; notes: string | null; next: string | null };
  evidence: Evidence[] | null; recommendationHref: string | null;
  professional: Row; quality: Row; valuation: Row; valuationView: Row; readiness: Row;
};
export function parseThesis(payload: unknown, requested: string): ThesisReaderData {
  const envelope = object(payload), data = object(envelope.data), links = object(envelope.links);
  const resolution = resolveIdentity("thesis", requested, data, links), symbol = knownSymbol(data.symbol);
  if (!resolution || !symbol || !identifier(data.instrument_id)) throw new Error("thesis identity unavailable");
  const lifecycle = object(data.lifecycle), buy = object(lifecycle.buy_case), review = object(data.latest_review);
  const conditions = rows(lifecycle.invalidation_conditions) ?? rows(data.invalidation_conditions);
  const quality = object(data.evidence_review), professional = object(data.professional_lifecycle_gates);
  return {
    id: text(data.thesis_id), resolution, symbol, version: text(data.thesis_version), status: text(data.status),
    summary: text(data.summary, "저장된 투자 논리 요약이 없습니다."), researchSummary: text(buy.summary, "") || null,
    researchSource: text(lifecycle.source), claims: strings(data.core_claims) ?? strings(buy.core_claims),
    catalysts: strings(lifecycle.catalysts), risks: strings(lifecycle.risks),
    conditions: conditions?.map(row => ({ text: text(row.condition, "조건 미정의"), state: conditionState(row.current_status) })) ?? null,
    review: { id: identifier(review.review_id), action: text(review.action), risk: text(review.risk_level), date: recordedDate(review.reviewed_at),
      summary: text(review.summary, "") || null, notes: text(review.change_notes, "") || null, next: recordedDate(review.next_review_date) },
    evidence: rows(data.evidence)?.map(row => {
      const item = evidence(row);
      if (item.type === "performance_outcome" || item.id.startsWith("performance-outcome-")) return { ...item, href: `/performance?q=${encodeURIComponent(symbol)}`, action: "종목 성과 목록" };
      if (!(item.id.startsWith("event-") || item.id.startsWith("sec-event-") || item.id.startsWith("ai-evidence-"))) return { ...item, href: null, action: "상세 연결 미제공" };
      return item;
    }) ?? null,
    recommendationHref: route("recommendations", data.created_from_recommendation_id) ?? safeApiLink(links.recommendation, "recommendations"),
    professional, quality, valuation: object(data.valuation_target_range), valuationView: object(lifecycle.valuation), readiness: object(lifecycle.readiness),
  };
}
export function thesisAttention(data: ThesisReaderData): string {
  if (data.conditions?.some(row => row.state === "triggered") || (count(data.professional.blocked_count) ?? 0) > 0 || (count(object(data.quality.summary).blocked_count) ?? 0) > 0) return "발동·차단 기록 확인";
  if (!data.conditions?.length || data.conditions.some(row => row.state === "unknown") || !data.review.id || !data.review.date) return "미확인 항목 확인";
  return "저장된 검토·근거 확인";
}
export function currencyValue(value: unknown, currency: unknown): string {
  const n = numeric(value), unit = text(currency, "");
  if (n === null) return "미측정";
  if (!/^[A-Z]{3}$/.test(unit)) return `${n.toLocaleString("ko-KR")} · 통화 미확인`;
  return new Intl.NumberFormat("ko-KR", { style: "currency", currency: unit, maximumFractionDigits: 2 }).format(n);
}

/** Reuse the existing deep valuation view only with its complete collection shape.
 * Missing data is never filled just to make the old renderer appear complete. */
export function fullValuation(value: Row): ValuationTargetRange | null {
  const methods = rows(value.methods), quality = object(value.valuation_quality);
  if (value.status !== "available" || !/^[A-Z]{3}$/.test(text(value.currency_code, ""))
    || !methods?.length || typeof value.summary !== "string"
    || typeof quality.label !== "string" || typeof quality.confidence_label !== "string"
    || count(quality.data_gap_count) === null || count(quality.warning_count) === null) return null;
  for (const method of methods) {
    const forecast = object(method.forecast_evidence), sotp = object(method.sotp_evidence), quality = object(method.data_quality);
    if (typeof method.method_label !== "string" || !rows(method.assumption_items) || !rows(method.sensitivity_cases)
      || typeof quality.status !== "string" || typeof quality.label !== "string" || typeof quality.confidence_label !== "string"
      || !strings(quality.warnings) || !strings(method.limitations)
      || typeof forecast.status !== "string" || !rows(forecast.scenarios)
      || typeof sotp.status !== "string" || !rows(sotp.components) || !rows(sotp.reported_segment_inputs)
      || !rows(sotp.reported_segment_allocations) || !rows(sotp.reported_segment_assumptions)
      || typeof object(sotp.segment_footnote_evidence).status !== "string"
      || !rows(object(sotp.segment_footnote_evidence).evidence_rows)) return null;
  }
  return value as unknown as ValuationTargetRange;
}
