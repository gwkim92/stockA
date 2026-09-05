// @vitest-environment node
import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadDiscovery } from "./discovery-data";
import { changedCycle, cycleGap, cycleSummary, currency, dateLabel, filterDiscovery, flattenMarket, marketAttention, observationState, parseDiscovery, priceAttention, ratioLabel, safeSource, type DiscoveryKind } from "./discovery-model";
const date = "2026-09-05";
const sample = (name: string) => JSON.parse(readFileSync(`../../docs/api/frontend/examples/${name}.json`, "utf8"));
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });
describe("actual repository discovery contracts", () => {
  it.each([["stocks", "stock-list"], ["cycles", "cycle-state-list"], ["market", "market-map"]])("parses %s without modifying the saved contract example", (kind, name) => {
    const source = sample(name), before = JSON.stringify(source);
    const parsed = parseDiscovery(kind as DiscoveryKind, source);
    expect(parsed.rows.length).toBeGreaterThan(0); expect(JSON.stringify(source)).toBe(before);
  });
  it("does not replace absent market snapshot date with generation or request date", () => {
    const source = sample("market-map"); source.data.snapshot_as_of_date = null;
    expect(parseDiscovery("market", source).asOfDate).toBeNull();
  });
  it.each([null, {}, { data: {} }, { data: { stocks: [null] } }, { data: { stocks: [{ symbol: "AAPL" }] } }])("rejects missing or malformed primary records", payload => expect(() => parseDiscovery("stocks", payload)).toThrow());
  it("rejects duplicate identities rather than silently dropping a record", () => {
    const source = sample("stock-list"); source.data.stocks.push(source.data.stocks[0]); expect(() => parseDiscovery("stocks", source)).toThrow();
  });
  it("distinguishes valid empty from failed or missing primary data", () => {
    expect(parseDiscovery("cycles", { data: { cycle_states: [] } }).rows).toEqual([]);
    expect(() => parseDiscovery("cycles", { data: {} })).toThrow();
  });
  it("rejects malformed nested market indicators", () => expect(() => parseDiscovery("market", { data: { groups: [{ group_code: "usd", indicators: null }] } })).toThrow());
});
describe("no synthetic investment conclusions", () => {
  it.each([null, undefined, "", "unknown", "not_available"])("does not call absent previous state %s a transition", previous => expect(changedCycle({ state: "expanding", previous_state: previous })).toBe(false));
  it("requires two observed different states", () => {
    expect(changedCycle({ state: "expanding", previous_state: "forming" })).toBe(true);
    expect(changedCycle({ state: "unknown", previous_state: "forming" })).toBe(false);
    expect(changedCycle({ state: "forming", previous_state: "forming" })).toBe(false);
  });
  it("keeps missing features different from measured zero", () => {
    expect(cycleGap({ features: { event_intensity: 0, price_momentum: 0, fundamental_quality: 0 } })).toBe(false);
    expect(cycleGap({ features: { event_intensity: 0 } })).toBe(true);
    expect(ratioLabel(0)).toBe("0%"); expect(ratioLabel(null)).toBe("미측정");
  });
  it("reports memberships, not unique stocks; missing counts and confidence stay unknown", () => {
    const rows = [{ instrument_count: 2, confidence: 0.8, top_symbols: ["AAPL"] }, { instrument_count: 2, confidence: null, top_symbols: ["AAPL"] }];
    expect(cycleSummary(rows)).toMatchObject({ memberships: 4, confidence: 0.8, confidenceCount: 1 });
    expect(cycleSummary([{}])).toMatchObject({ memberships: null, confidence: null });
    expect(cycleSummary([]).memberships).toBeNull();
  });
  it("does not invent live stock prices or unknown currencies", () => {
    expect(currency(null, "USD")).toBe("가격 미확인"); expect(currency(0, "USD")).toBe("가격 미확인");
    expect(currency(NaN, "USD")).toBe("가격 미확인"); expect(currency(10, null)).toContain("통화 미확인");
    expect(priceAttention({ latest_price: { close: 10, trade_date: date } }, date)).toBe(false);
    expect(priceAttention({ latest_price: { close: null, trade_date: date } }, date)).toBe(true);
  });
  it.each([["2026-09-04", "historical"], ["2026-09-06", "future"], [date, "matching"], ["2026-02-30", "unknown"]])("labels source date %s without a new freshness threshold", (observed, expected) => expect(observationState(observed, date)).toBe(expected));
  it("retains unknown comparison dates", () => expect(dateLabel(date, null)).toContain("미확인"));
  it("does not mark an empty or undated market observation as ready", () => {
    expect(marketAttention({}, date)).toBe(true);
    expect(marketAttention({ freshness_status: "fresh", latest_value: 3, latest_observation_date: "2027-01-01" }, date)).toBe(true);
    expect(marketAttention({ freshness_status: "fresh", latest_value: -0.5, latest_observation_date: date }, date)).toBe(false);
  });
  it("search/filter preserves source order and does not mutate input", () => {
    const rows = [{ instrument_id: "a", symbol: "MSFT", name: "Microsoft", position: null }, { instrument_id: "b", symbol: "AAPL", name: "Apple", position: { portfolio_name: "Paper" } }];
    const before = JSON.stringify(rows);
    expect(filterDiscovery(rows, "stocks", "", "all", "", date)).toEqual(rows);
    expect(filterDiscovery(rows, "stocks", "apple", "held", "", date).map(row => row.symbol)).toEqual(["AAPL"]);
    expect(JSON.stringify(rows)).toBe(before);
  });
  it("filters cycles by observed change and searches actual linked symbols", () => {
    const rows = parseDiscovery("cycles", sample("cycle-state-list")).rows;
    expect(filterDiscovery(rows, "cycles", "AAPL", "all", "", date)).toHaveLength(1);
    expect(filterDiscovery(rows, "cycles", "", "changed", "", date).every(changedCycle)).toBe(true);
  });
  it("retains group identity and protects primary source links", () => {
    expect(flattenMarket([{ group_code: "rates", group_name: "금리", indicators: [{ indicator_code: "DGS10" }] }])[0].group_code).toBe("rates");
    expect(safeSource("javascript:alert(1)")).toBeNull(); expect(safeSource("https://u:p@example.org")).toBeNull();
    expect(safeSource("https://example.org/report")).toBe("https://example.org/report");
  });
});
describe("bounded raw discovery reads", () => {
  it("a missing endpoint does not fall back to a fake healthy market", async () => {
    const fetcher = vi.fn(async () => new Response("private error", { status: 404 })) as typeof fetch;
    const result = await loadDiscovery("market", { fetcher }); expect(result.issue).toBe("http"); expect(result.data).toBeNull(); expect(JSON.stringify(result)).not.toContain("private");
  });
  it("never exports connection failures or read tokens", async () => {
    vi.stubEnv("STOCKANALYSIS_FRONTEND_API_READ_TOKEN", "hidden-token");
    const fetcher = vi.fn(async () => { throw new Error("secret-password"); }) as typeof fetch;
    const result = await loadDiscovery("stocks", { fetcher }); expect(result.issue).toBe("network"); expect(JSON.stringify(result)).not.toContain("secret");
    expect(fetcher).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ method: "GET", cache: "no-store", redirect: "error", headers: expect.objectContaining({ Authorization: "Bearer hidden-token" }) }));
  });
  it("invalid JSON remains a local invalid-data state", async () => expect((await loadDiscovery("cycles", { fetcher: vi.fn(async () => new Response("bad")) as typeof fetch })).issue).toBe("invalid"));
  it("body parsing is inside the deadline and abort clears its timer", async () => {
    vi.useFakeTimers(); let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn(async (_url, init) => { signal = init?.signal; return { ok: true, json: () => new Promise(() => {}) }; }) as unknown as typeof fetch;
    const promise = loadDiscovery("stocks", { fetcher, timeoutMs: 20 }); await vi.advanceTimersByTimeAsync(21);
    expect((await promise).issue).toBe("timeout"); expect(signal).toMatchObject({ aborted: true }); expect(vi.getTimerCount()).toBe(0);
  });
  it("honors the real contract snapshot rather than fetch time", async () => {
    const source = sample("stock-list"), fetcher = vi.fn(async () => Response.json(source)) as typeof fetch;
    const result = await loadDiscovery("stocks", { now: new Date(`${date}T00:00:00Z`), fetcher });
    expect(result.data?.asOfDate).toBe(source.data.as_of_date); expect(result.requestedDate).toBe(date);
  });
});
