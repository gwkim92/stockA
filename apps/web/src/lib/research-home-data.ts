/** Server-side home reads. Intentionally do not apply zero/ready DTO defaults. */
import {
  HOME_FEEDS, parseHomeFeed, unavailableFeed,
  type HomeFeed, type HomeFeedKey, type ResearchHomeSnapshot,
} from "./research-home-model";

const TIMEOUT_MS = 5_000;
class HomeHttpError extends Error {}
class HomePayloadError extends Error {}

export async function readHomeFeed(
  key: HomeFeedKey,
  path: string,
  requestedDate: string,
  options: { baseUrl: string; readToken?: string; timeoutMs?: number; fetcher?: typeof fetch },
): Promise<HomeFeed> {
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? TIMEOUT_MS;
  let timedOut = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
      reject(new Error("home source deadline"));
    }, timeoutMs);
  });
  try {
    const request = async () => {
      const headers: Record<string, string> = { Accept: "application/json" };
      if (options.readToken) headers.Authorization = `Bearer ${options.readToken}`;
      const response = await (options.fetcher ?? fetch)(`${options.baseUrl}${path}`, {
        headers, cache: "no-store", redirect: "error", signal: controller.signal,
      });
      if (!response.ok) throw new HomeHttpError();
      try {
        return parseHomeFeed(key, await response.json(), requestedDate);
      } catch {
        throw new HomePayloadError();
      }
    };
    // The deadline includes stalled body parsing, not just receipt of headers.
    return await Promise.race([request(), deadline]);
  } catch (error) {
    return unavailableFeed(key, timedOut ? "timeout" : error instanceof HomeHttpError ? "http"
      : error instanceof HomePayloadError ? "invalid" : "network");
  } finally {
    clearTimeout(timer);
  }
}

export async function loadResearchHomeSnapshot(
  options: { now?: Date; fetcher?: typeof fetch; timeoutMs?: number } = {},
): Promise<ResearchHomeSnapshot> {
  const requestedDate = (options.now ?? new Date()).toISOString().slice(0, 10);
  const baseUrl = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? "http://127.0.0.1:8765").replace(/\/$/, "");
  const readToken = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const paths: Record<HomeFeedKey, string> = {
    cycles: `/api/cycles?asOfDate=${requestedDate}`,
    recommendations: "/api/recommendations",
    news: `/api/ai/news-clusters?asOfDate=${requestedDate}&limit=4`,
    portfolio: "/api/dashboard/today",
  };
  const feeds = await Promise.all(HOME_FEEDS.map((key) => readHomeFeed(key, paths[key], requestedDate, {
    baseUrl, readToken, fetcher: options.fetcher, timeoutMs: options.timeoutMs,
  })));
  return { requestedDate, feeds: Object.fromEntries(feeds.map((feed) => [feed.key, feed])) as Record<HomeFeedKey, HomeFeed> };
}
