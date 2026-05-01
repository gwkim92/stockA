import type {
  ApiResponse,
  CycleStateListData,
  DailyCockpitData,
  DataHealthData,
  PortfolioCoverageData,
  RecommendationDetailData,
  RemediationTicketsData,
  ThesisDetailData,
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
  const response = await fetch(`${fixtureBaseUrl()}${path}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
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

export function getCycleStates() {
  return fetchFrontendPayload<CycleStateListData>("/api/cycles?asOfDate=2024-11-01");
}

export function getRecommendationDetail(recommendationId: string) {
  return fetchFrontendPayload<RecommendationDetailData>(`/api/recommendations/${recommendationId}`);
}

export function getThesisDetail(thesisId: string) {
  return fetchFrontendPayload<ThesisDetailData>(`/api/theses/${thesisId}`);
}

export function getPortfolioCoverage() {
  return fetchFrontendPayload<PortfolioCoverageData>(
    "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
  );
}
