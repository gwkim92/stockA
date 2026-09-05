// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadResearchHomeSnapshot, readHomeFeed } from "./research-home-data";
import {
  HOME_FEEDS, FEED_LISTS, changedCycles, count, feedCaption, fraction, homeHealth,
  isoDate, parseHomeFeed, recommendationStatus, unavailableFeed,
  type HomeFeedKey, type ResearchHomeSnapshot,
} from "./research-home-model";

const date = "2026-09-05";
const envelope = (key: HomeFeedKey, data: Record<string, unknown> = {}) => ({
  contract_version: "frontend-api-v0.1", generated_at: `${date}T12:00:00Z`,
  data: { as_of_date: date, [FEED_LISTS[key]]: [], ...data }, links: {},
});
const available = (key: HomeFeedKey) => parseHomeFeed(key, envelope(key), date);
const options = (fetcher: typeof fetch) => ({ baseUrl: "http://127.0.0.1:8765", timeoutMs: 20, fetcher });
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); vi.restoreAllMocks(); });

describe("honest research presentation", () => {
  it.each([undefined, null, NaN, Infinity, -1, 1.5, "3", true])("does not turn %s into zero", (value) => expect(count(value)).toBeNull());
  it("preserves a measured zero and rejects invalid coverage", () => {
    expect(count(0)).toBe(0); expect(fraction(0)).toBe(0); expect(fraction(1.1)).toBeNull();
  });
  it.each(["2026-02-30", "2026-13-01", "2026-09-05junk", "", null])("rejects invalid evidence date %s", (value) => expect(isoDate(value)).toBeNull());
  it("does not use generated_at to freshen old evidence", () => {
    const feed = parseHomeFeed("news", envelope("news", { as_of_date: "2025-01-01" }), date);
    expect(feed.dateState).toBe("historical"); expect(feedCaption(feed)).toContain("과거 기준 · 2025-01-01");
  });
  it("keeps missing and future analysis dates explicit", () => {
    const missing = parseHomeFeed("cycles", envelope("cycles", { as_of_date: null }), date);
    const future = parseHomeFeed("cycles", envelope("cycles", { as_of_date: "2027-01-01" }), date);
    expect(missing.dateState).toBe("unknown"); expect(feedCaption(missing)).toContain("기준일 미확인");
    expect(future.dateState).toBe("future"); expect(feedCaption(future)).toContain("판단에 사용하지 마세요");
  });
  it("distinguishes a successful empty list from an unavailable feed", () => {
    expect(available("news").data?.clusters).toEqual([]);
    expect(unavailableFeed("news", "http").data).toBeNull();
  });
  it.each([{}, null, { data: {} }, { data: { clusters: [null] } }])("rejects malformed envelopes", (payload) => expect(() => parseHomeFeed("news", payload, date)).toThrow());
  it("requires both cycle states before claiming a transition", () => {
    const feed = parseHomeFeed("cycles", envelope("cycles", { cycle_states: [
      { state: "expanding", previous_state: "forming" },
      { state: "expanding", previous_state: "expanding" },
      { state: "expanding", previous_state: null },
      { state: "expanding", previous_state: "unknown" },
    ] }), date);
    expect(changedCycles(feed)).toHaveLength(1);
  });
  it("never makes source-blocked or unknown-boundary candidates green", () => {
    const row = { decision_boundary: { paper_validation_input_allowed: true }, evidence_quality: { source_blocker: { blocked: true } } };
    expect(recommendationStatus(row, available("recommendations"))).toBe("source_limited");
    expect(recommendationStatus({}, available("recommendations"))).toBe("watch");
    expect(recommendationStatus({ decision_boundary: { paper_validation_input_allowed: true } }, available("recommendations"))).toBe("watch");
  });
  it("does not promote historical evidence and preserves backend order", () => {
    const row = { evidence_quality: { source_blocker: { blocked: false } }, decision_boundary: { paper_validation_input_allowed: true } };
    expect(recommendationStatus(row, available("recommendations"))).toBe("ready");
    expect(recommendationStatus(row, { ...available("recommendations"), dateState: "historical" })).toBe("watch");
    const payload = envelope("recommendations", { recommendations: [{ recommendation_id: "r2" }, { recommendation_id: "r1" }] });
    const original = JSON.stringify(payload);
    expect(parseHomeFeed("recommendations", payload, date).data?.recommendations).toEqual(payload.data.recommendations);
    expect(JSON.stringify(payload)).toBe(original);
  });
  it("missing pipeline counts do not mean healthy", () => {
    const snapshot = { requestedDate: date, feeds: Object.fromEntries(HOME_FEEDS.map((key) => [key, available(key)])) } as ResearchHomeSnapshot;
    expect(homeHealth(snapshot)).toBe("작업 상태 미확인");
    snapshot.feeds.portfolio.data!.attention_summary = { failed_pipeline_count: 0 };
    expect(homeHealth(snapshot)).toBe("조회된 작업에서 실패 없음");
    snapshot.feeds.news = unavailableFeed("news", "network");
    expect(homeHealth(snapshot)).toBe("일부 영역을 불러오지 못했습니다");
  });
  it("marks paginated responses as partial rather than total counts", () => {
    const feed = parseHomeFeed("news", { ...envelope("news"), pagination: { has_more: true } }, date);
    expect(feedCaption(feed)).toContain("일부 결과");
  });
});

describe("independent bounded server reads", () => {
  it("isolates an HTTP failure and does not expose its response body", async () => {
    const fetcher = vi.fn(async (url: string | URL | Request) => {
      const path = String(url);
      if (path.includes("news-clusters")) return new Response("secret-internal-error", { status: 503 });
      const key: HomeFeedKey = path.includes("/cycles") ? "cycles" : path.includes("/recommendations") ? "recommendations" : "portfolio";
      return Response.json(envelope(key));
    }) as unknown as typeof fetch;
    const snapshot = await loadResearchHomeSnapshot({ now: new Date(`${date}T12:00:00Z`), fetcher });
    expect(snapshot.feeds.news.issue).toBe("http");
    expect(snapshot.feeds.cycles.data).not.toBeNull(); expect(snapshot.feeds.recommendations.data).not.toBeNull();
    expect(fetcher).toHaveBeenCalledTimes(4); expect(JSON.stringify(snapshot)).not.toContain("secret-internal-error");
  });
  it("handles all-feed failure without rejecting the home snapshot", async () => {
    const fetcher = vi.fn(async () => { throw new Error("postgres://private-user:password@host"); }) as typeof fetch;
    const snapshot = await loadResearchHomeSnapshot({ fetcher });
    expect(Object.values(snapshot.feeds).every((feed) => feed.data === null)).toBe(true);
    expect(JSON.stringify(snapshot)).not.toContain("password"); expect(homeHealth(snapshot)).toContain("연결을 확인");
  });
  it("aborts a stalled request at the deadline", async () => {
    vi.useFakeTimers();
    let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn((_url, init) => { signal = init?.signal; return new Promise<Response>(() => {}); }) as typeof fetch;
    const pending = readHomeFeed("news", "/api/news", date, options(fetcher));
    await vi.advanceTimersByTimeAsync(21);
    expect((await pending).issue).toBe("timeout"); expect(signal).toMatchObject({ aborted: true });
    expect(vi.getTimerCount()).toBe(0);
  });
  it("includes a stalled JSON body in the deadline", async () => {
    vi.useFakeTimers();
    const fetcher = vi.fn(async () => ({ ok: true, json: () => new Promise(() => {}) })) as unknown as typeof fetch;
    const pending = readHomeFeed("news", "/api/news", date, options(fetcher));
    await vi.advanceTimersByTimeAsync(21);
    expect((await pending).issue).toBe("timeout"); expect(vi.getTimerCount()).toBe(0);
  });
  it("uses only no-store authenticated GET requests and refuses redirects", async () => {
    const fetcher = vi.fn(async () => Response.json(envelope("news"))) as typeof fetch;
    const feed = await readHomeFeed("news", "/api/news", date, { ...options(fetcher), readToken: "test-read-token" });
    expect(feed.issue).toBeNull();
    expect(fetcher).toHaveBeenCalledWith("http://127.0.0.1:8765/api/news", expect.objectContaining({
      cache: "no-store", redirect: "error", headers: { Accept: "application/json", Authorization: "Bearer test-read-token" },
    }));
    expect(JSON.stringify(feed)).not.toContain("test-read-token");
  });
  it("classifies invalid JSON without leaking payload text", async () => {
    const fetcher = vi.fn(async () => new Response("sensitive-not-json")) as typeof fetch;
    const feed = await readHomeFeed("news", "/api/news", date, options(fetcher));
    expect(feed.issue).toBe("invalid"); expect(JSON.stringify(feed)).not.toContain("sensitive");
  });
});
