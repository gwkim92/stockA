// @vitest-environment node
import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { conditionState, currencyValue, filterExcerpts, fullValuation, identifier, nextReview, parseSource, parseThesis, recordedDate, resolveIdentity, safeApiLink, thesisAttention } from "./research-reader-model";
import { loadReader } from "./research-reader-data";
const example = (name: string) => JSON.parse(readFileSync(`../../docs/api/frontend/examples/${name}.json`, "utf8"));
const source = () => example("source-document-detail");
const thesis = () => example("thesis-detail");
const today = "2026-09-05";
afterEach(() => { vi.useRealTimers(); vi.unstubAllEnvs(); });
describe("existing reader contracts", () => {
  it("preserves original source text without guessing a topic", () => {
    const input = source(), before = JSON.stringify(input);
    const data = parseSource(input, input.data.document_id);
    expect(data.title).toBe(input.data.title); expect(data.excerpts?.[0].summary).toBe(input.data.excerpts[0].summary);
    expect(data.koreanSummary).toBeNull(); expect(JSON.stringify(input)).toBe(before);
  });
  it("reads the saved thesis without inventing lifecycle counters, risk or currency", () => {
    const input = thesis(), before = JSON.stringify(input), data = parseThesis(input, input.data.thesis_id);
    expect(data.claims).toEqual(input.data.core_claims); expect(data.professional.gate_count).toBeUndefined();
    expect(data.catalysts).toBeNull(); expect(data.valuation.currency_code).toBeUndefined(); expect(JSON.stringify(input)).toBe(before);
  });
  it("keeps missing summaries and titles separate", () => {
    const input = source(); input.data.korean_title = "저장된 한국어 제목";
    expect(parseSource(input, input.data.document_id).koreanSummary).toBeNull();
  });
  it("never exports internal storage addresses or arbitrary extra fields", () => {
    const input = source(); input.data.storage_uri = "postgresql://private:password@host/db"; input.data.debug_secret = "not-browser-data";
    const result = JSON.stringify(parseSource(input, input.data.document_id));
    expect(result).not.toMatch(/password|not-browser-data|postgresql/);
  });
  it.each([false, true, null, "true"])("a raw-download flag %s cannot create a browser URL", flag => {
    const input = source(); input.data.access_policy.browser_download_enabled = flag;
    const data = parseSource(input, input.data.document_id);
    expect(data.download).toBe(flag === false ? "restricted" : flag === true ? "unavailable" : "unknown");
    expect(data).not.toHaveProperty("downloadUrl");
  });
  it("does not use generated_at as a publication or review date", () => {
    const input = source(); delete input.data.filed_at; delete input.data.retrieval.fetched_at;
    expect(parseSource(input, input.data.document_id)).toMatchObject({ filedAt: null, fetchedAt: null });
    const t = thesis(); delete t.data.latest_review.reviewed_at;
    expect(parseThesis(t, t.data.thesis_id).review.date).toBeNull();
  });
  it("distinguishes missing and empty excerpt collections", () => {
    const input = source(); input.data.excerpts = []; expect(parseSource(input, input.data.document_id).excerpts).toEqual([]);
    delete input.data.excerpts; expect(parseSource(input, input.data.document_id).excerpts).toBeNull();
  });
  it("rejects duplicate or unidentifiable excerpts", () => {
    const input = source(); input.data.excerpts.push(input.data.excerpts[0]); expect(() => parseSource(input, input.data.document_id)).toThrow();
  });
});
describe("conditions are not inferred decisions", () => {
  it.each([undefined, null, "unknown", "needs_review", "unavailable", true, 1])("does not count %s as a triggered condition", value => expect(conditionState(value)).toBe("unknown"));
  it("requires explicit triggered/not_triggered values", () => { expect(conditionState("triggered")).toBe("triggered"); expect(conditionState("not_triggered")).toBe("not_triggered"); });
  it("does not call an unknown condition blocked or ready", () => {
    const input = thesis(); input.data.invalidation_conditions = [{ condition: "growth", current_status: "unknown" }];
    expect(thesisAttention(parseThesis(input, input.data.thesis_id))).toBe("미확인 항목 확인");
  });
  it("preserves a reported trigger and its independent warning", () => {
    const input = thesis(); input.data.invalidation_conditions = [{ condition: "growth", current_status: "triggered" }];
    expect(thesisAttention(parseThesis(input, input.data.thesis_id))).toBe("발동·차단 기록 확인");
  });
  it("does not fabricate a next review date or a dollar currency", () => {
    expect(nextReview(undefined, today)).toBe("미지정"); expect(nextReview("2026-09-01", today)).toContain("예정일 지남");
    expect(currencyValue(100, undefined)).toBe("100 · 통화 미확인"); expect(currencyValue(null, "USD")).toBe("미측정");
  });
  it.each(["2026-02-30", "2026-02-30T00:00:00Z", "2026-09-05junk", "not-a-date"])("rejects malformed timestamp %s", date => expect(recordedDate(date)).toBeNull());
});
describe("safe and compatible source identities", () => {
  it.each(["", "..", "a/b", "a\\b", "x?token=y", "x#id", "a%2Fb", "\nunsafe"])("rejects unsafe identifier %s", value => expect(identifier(value)).toBeNull());
  it("canonical IDs must match rather than substitute a different record", () => {
    const input = thesis(); expect(() => parseThesis(input, "thesis-999")).toThrow();
    const document = source(); expect(() => parseSource(document, "different-document")).toThrow();
  });
  it("preserves the backend numeric and bootstrap aliases", () => {
    expect(resolveIdentity("thesis", "3", { thesis_id: "thesis-3", symbol: "AAPL" }, {})).toBe("alias");
    expect(resolveIdentity("thesis", "AAPL-bootstrap-v1", { thesis_id: "thesis-3", symbol: "AAPL" }, {})).toBe("alias");
    expect(resolveIdentity("thesis", "AAPL-bootstrap-v1", { thesis_id: "thesis-3", symbol: "MSFT" }, {})).toBeNull();
  });
  it("numeric-to-external source resolution needs the backend request self-link", () => {
    expect(resolveIdentity("source", "source-document-7", { document_id: "aapl-external" }, { source_document: "/api/source-documents/source-document-7" })).toBe("alias");
    expect(resolveIdentity("source", "source-document-7", { document_id: "aapl-external" }, {})).toBeNull();
  });
  it.each(["https://evil.test/api/theses/t1", "/api/theses/../admin", "/api/theses/t1?token=x", "/api/theses/a%2Fb", "/api/theses/%ZZ"])("rejects unexpected supplied link %s", value => expect(safeApiLink(value, "theses")).toBeNull());
  it("accepts only a same-resource safe API link", () => expect(safeApiLink("/api/theses/thesis-1", "theses")).toBe("/theses/thesis-1"));
  it("labels performance links as filtered lists, not an exact outcome view", () => {
    const input = thesis(); const data = parseThesis(input, input.data.thesis_id);
    expect(data.evidence?.[1]).toMatchObject({ href: "/performance?q=AAPL", action: "종목 성과 목록" });
  });
  it("literal excerpt search preserves content and order", () => {
    const input = source(), data = parseSource(input, input.data.document_id), before = JSON.stringify(data.excerpts);
    expect(filterExcerpts(data.excerpts!, "10-K item 7")).toHaveLength(1);
    expect(filterExcerpts(data.excerpts!, ".*")).toHaveLength(0); expect(JSON.stringify(data.excerpts)).toBe(before);
  });
});
describe("bounded authenticated reads", () => {
  it("invalid path parameters fail before IO", async () => {
    const fetcher = vi.fn(); expect((await loadReader("source", "../admin", { fetcher })).issue).toBe("identifier"); expect(fetcher).not.toHaveBeenCalled();
  });
  it.each([404, 403, 503])("HTTP %s is not replaced with a fake healthy document", async status => {
    const result = await loadReader("source", "doc1", { fetcher: vi.fn(async () => new Response("secret-body", { status })) as typeof fetch });
    expect(result.issue).toBe(status === 404 ? "not-found" : "http"); expect(result.data).toBeNull(); expect(JSON.stringify(result)).not.toContain("secret-body");
  });
  it("sends credentials server-side only and refuses redirects", async () => {
    const input = source(), fetcher = vi.fn(async () => Response.json(input)) as typeof fetch;
    vi.stubEnv("STOCKANALYSIS_FRONTEND_API_READ_TOKEN", "private-read-token");
    const result = await loadReader("source", input.data.document_id, { fetcher });
    expect(result.issue).toBeNull(); expect(fetcher).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ method: "GET", cache: "no-store", redirect: "error", headers: expect.objectContaining({ Authorization: "Bearer private-read-token" }) }));
    expect(JSON.stringify(result)).not.toContain("private-read-token");
  });
  it("a stalled JSON body is timed out and aborted", async () => {
    vi.useFakeTimers(); let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn(async (_url, init) => { signal = init?.signal; return { ok: true, json: () => new Promise(() => {}) }; }) as unknown as typeof fetch;
    const pending = loadReader("source", "doc1", { fetcher, timeoutMs: 20 }); await vi.advanceTimersByTimeAsync(21);
    expect((await pending).issue).toBe("timeout"); expect(signal).toMatchObject({ aborted: true }); expect(vi.getTimerCount()).toBe(0);
  });
  it("malformed JSON is a local invalid state", async () => {
    expect((await loadReader("thesis", "thesis-1", { fetcher: vi.fn(async () => new Response("bad-json")) as typeof fetch })).issue).toBe("invalid");
  });
});

describe("existing deep valuation remains reachable", () => {
  const valuation = () => JSON.parse(readFileSync("tests/e2e/recommendation-memo-fixture.json", "utf8")).recommendation.valuation_target_range;
  it("returns the complete existing valuation unchanged", () => {
    const value = valuation(), before = JSON.stringify(value);
    expect(fullValuation(value)).toBe(value); expect(JSON.stringify(value)).toBe(before);
  });
  it("does not fabricate missing currency or deep collection shape", () => {
    const noCurrency = valuation(); delete noCurrency.currency_code; expect(fullValuation(noCurrency)).toBeNull();
    const missing = valuation(); delete missing.methods[0].forecast_evidence.scenarios; expect(fullValuation(missing)).toBeNull();
  });
});
