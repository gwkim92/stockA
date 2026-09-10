// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { proxyModelSettings } from "./model-settings-proxy";

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });
const req = (origin: string, method = "PATCH", body = "{}") => new NextRequest("http://localhost:13309/api/ai-model-settings", { method, headers: { origin, host: "localhost:13309", "content-type": "application/json" }, body });
describe("model settings browser boundary", () => {
  it("rejects cross-origin requests before forwarding credentials", async () => {
    const fetcher = vi.fn(); vi.stubGlobal("fetch", fetcher);
    expect((await proxyModelSettings(req("https://evil.example"))).status).toBe(403);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("exchanges one-time code for HttpOnly cookie without exposing credentials", async () => {
    vi.stubEnv("STOCKANALYSIS_FRONTEND_API_READ_TOKEN", "private-read-token");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({ session: "a".repeat(43) })));
    const response = await proxyModelSettings(req("http://localhost:13309", "POST", '{"code":"temporary"}'), true);
    expect(await response.json()).toEqual({ authorized: true });
    const cookie = response.headers.get("set-cookie")!;
    expect(cookie).toContain("HttpOnly"); expect(cookie).toContain("SameSite=strict");
    expect(cookie).not.toContain("private-read-token");
  });
  it("does not forward oversized bodies or service errors", async () => {
    vi.stubEnv("STOCKANALYSIS_FRONTEND_API_READ_TOKEN", "private-read-token");
    const fetcher = vi.fn(); vi.stubGlobal("fetch", fetcher);
    expect((await proxyModelSettings(req("http://localhost:13309", "PATCH", "x".repeat(8193)))).status).toBe(413);
    expect(fetcher).not.toHaveBeenCalled();
  });
});
