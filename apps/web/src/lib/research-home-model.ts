/** Presentation only: never changes backend ranks, scores, or permissions. */
export const HOME_FEEDS = ["cycles", "recommendations", "news", "portfolio"] as const;
export type HomeFeedKey = (typeof HOME_FEEDS)[number];
export type DataRecord = Record<string, unknown>;
export type EvidenceDateState = "current" | "historical" | "future" | "unknown";
export type HomeFeed = {
  key: HomeFeedKey;
  data: DataRecord | null;
  issue: "timeout" | "http" | "invalid" | "network" | null;
  asOfDate: string | null;
  dateState: EvidenceDateState;
  generatedAt: string | null;
  limited: boolean;
};
export type ResearchHomeSnapshot = {
  requestedDate: string;
  feeds: Record<HomeFeedKey, HomeFeed>;
};

export const FEED_LABELS: Record<HomeFeedKey, string> = {
  cycles: "시장 사이클", recommendations: "투자 후보", news: "뉴스 근거", portfolio: "보유 재검토",
};
export const FEED_LISTS: Record<HomeFeedKey, string> = {
  cycles: "cycle_states", recommendations: "recommendations", news: "clusters", portfolio: "top_actions",
};

export function record(value: unknown): DataRecord {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as DataRecord : {};
}
export function text(value: unknown, fallback = "미확인"): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}
export function rows(value: unknown): DataRecord[] {
  return Array.isArray(value) ? value.filter((row) => row !== null && typeof row === "object" && !Array.isArray(row)) : [];
}
export function count(value: unknown): number | null {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0 ? value : null;
}
export function fraction(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1 ? value : null;
}
export function isoDate(value: unknown): string | null {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value ? value : null;
}

export function parseHomeFeed(key: HomeFeedKey, payload: unknown, requestedDate: string): HomeFeed {
  const envelope = record(payload);
  const data = record(envelope.data);
  const list = data[FEED_LISTS[key]];
  if (!Array.isArray(list) || rows(list).length !== list.length) throw new Error("invalid home feed");
  const identityField: Record<HomeFeedKey, string> = {
    cycles: "theme_key", recommendations: "recommendation_id", news: "evidence_id", portfolio: "symbol",
  };
  if (rows(list).some((row) => !text(row[identityField[key]], ""))) throw new Error("missing row identity");
  // A response-generation timestamp is NOT the date of its underlying evidence.
  const asOfDate = isoDate(data.as_of_date);
  const dateState = !asOfDate ? "unknown" : asOfDate > requestedDate ? "future"
    : asOfDate < requestedDate ? "historical" : "current";
  return {
    key, data, issue: null, asOfDate, dateState,
    generatedAt: typeof envelope.generated_at === "string" ? envelope.generated_at : null,
    limited: record(envelope.pagination).has_more === true,
  };
}

export function unavailableFeed(key: HomeFeedKey, issue: HomeFeed["issue"]): HomeFeed {
  return { key, data: null, issue, asOfDate: null, dateState: "unknown", generatedAt: null, limited: false };
}
export function feedCaption(feed: HomeFeed): string {
  if (!feed.data) return feed.issue === "timeout" ? "응답 지연 · 이 영역만 불러오지 못했습니다" : "연결 확인 필요 · 이 영역만 불러오지 못했습니다";
  if (feed.dateState === "unknown") return "분석 기준일 미확인 · 최신 자료로 간주하지 않습니다";
  if (feed.dateState === "future") return `기준일 오류 · ${feed.asOfDate} · 판단에 사용하지 마세요`;
  const suffix = feed.limited ? " · 일부 결과" : "";
  return `${feed.dateState === "historical" ? "과거 기준" : "조회 기준일과 일치"} · ${feed.asOfDate}${suffix}`;
}
export function changedCycles(feed: HomeFeed): DataRecord[] {
  return rows(feed.data?.cycle_states).filter((cycle) => {
    const current = text(cycle.state, "");
    const previous = text(cycle.previous_state, "");
    return current && previous && current !== "unknown" && previous !== "unknown" && current !== previous;
  });
}
export function recommendationStatus(row: DataRecord, feed: HomeFeed): "source_limited" | "watch" | "ready" {
  if (record(record(row.evidence_quality).source_blocker).blocked === true) return "source_limited";
  if (feed.dateState !== "current") return "watch";
  return record(record(row.evidence_quality).source_blocker).blocked === false
    && record(row.decision_boundary).paper_validation_input_allowed === true ? "ready" : "watch";
}
export function homeHealth(snapshot: ResearchHomeSnapshot): string {
  const feeds = Object.values(snapshot.feeds);
  if (feeds.every((feed) => !feed.data)) return "분석 데이터 연결을 확인해 주세요";
  if (feeds.some((feed) => !feed.data)) return "일부 영역을 불러오지 못했습니다";
  if (feeds.some((feed) => feed.dateState !== "current")) return "분석 기준일을 확인해 주세요";
  const failed = count(record(snapshot.feeds.portfolio.data?.attention_summary).failed_pipeline_count);
  if (failed === null) return "작업 상태 미확인";
  return failed > 0 ? "일부 수집·분석 작업 확인 필요" : "조회된 작업에서 실패 없음";
}
