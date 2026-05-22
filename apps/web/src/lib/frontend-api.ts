import type {
  ApiResponse,
  AiEvidenceNeighborhoodData,
  AiEvidenceDetailData,
  AiNewsClusterListData,
  CycleStateListData,
  DailyCockpitData,
  DataHealthData,
  EventListData,
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

export async function fetchFrontendPayload<TData>(path: string): Promise<ApiResponse<TData>> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const readToken = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  if (readToken) {
    headers.Authorization = `Bearer ${readToken}`;
  }

  const response = await fetch(`${fixtureBaseUrl()}${path}`, {
    cache: "no-store",
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

  return (await response.json()) as ApiResponse<TData>;
}

export async function getCockpitSnapshot() {
  const [dashboard, tickets, health] = await Promise.all([
    fetchFrontendPayload<DailyCockpitData>("/api/dashboard/today"),
    fetchFrontendPayload<RemediationTicketsData>("/api/remediation-tickets?status=open"),
    fetchFrontendPayload<DataHealthData>("/api/data-health"),
  ]);

  return { dashboard, tickets, health };
}

export function getRemediationTickets() {
  return fetchFrontendPayload<RemediationTicketsData>("/api/remediation-tickets?status=open");
}

export function getDataHealth() {
  return fetchFrontendPayload<DataHealthData>("/api/data-health");
}

export function getStocks() {
  return fetchFrontendPayload<StockListData>("/api/stocks");
}

export function getStockDetail(symbol: string) {
  return fetchFrontendPayload<StockDetailData>(`/api/stocks/${encodeURIComponent(symbol)}`);
}

export function getAiEvidenceNeighborhood(symbol: string) {
  return fetchFrontendPayload<AiEvidenceNeighborhoodData>(
    `/api/ai/evidence-neighborhoods/${encodeURIComponent(symbol)}`,
  );
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

export function getRecommendations() {
  return fetchFrontendPayload<RecommendationListData>("/api/recommendations");
}

export function getRecommendationDetail(recommendationId: string) {
  return fetchFrontendPayload<RecommendationDetailData>(`/api/recommendations/${recommendationId}`);
}

export function getThesisDetail(thesisId: string) {
  return fetchFrontendPayload<ThesisDetailData>(`/api/theses/${thesisId}`);
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
