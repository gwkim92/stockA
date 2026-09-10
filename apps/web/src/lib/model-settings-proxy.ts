import { NextRequest, NextResponse } from "next/server";

const COOKIE = "stockanalysis_model_manager";
const SESSION_SECONDS = 30 * 24 * 3600;

export function sameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (!origin || request.headers.get("sec-fetch-site") === "cross-site") return false;
  try {
    const parsed = new URL(origin);
    const secureTransport = parsed.protocol === "https:" || (parsed.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname));
    return secureTransport && parsed.host === request.headers.get("host");
  } catch { return false; }
}

export async function proxyModelSettings(request: NextRequest, sessionRoute = false) {
  const error = (message: string, status: number) => NextResponse.json({ error: message }, { status, headers: { "Cache-Control": "no-store" } });
  if (request.method !== "GET" && !sameOrigin(request)) return error("HTTPS 또는 로컬 SSH 터널의 같은 페이지에서 요청해 주세요.", 403);
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  if (!token) return error("모델 설정 서버 연결이 구성되지 않았습니다.", 503);
  let body: string | undefined;
  if (["POST", "PATCH"].includes(request.method)) {
    if (!request.headers.get("content-type")?.startsWith("application/json")) return error("JSON 요청이 필요합니다.", 415);
    // Stream with a hard cap; never buffer arbitrary public request bodies.
    const reader = request.body?.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    if (reader) {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > 8192) { await reader.cancel(); return error("요청이 너무 큽니다.", 413); }
        chunks.push(value);
      }
    }
    body = Buffer.concat(chunks).toString("utf8");
  }
  try {
    const base = process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL || "http://127.0.0.1:8765";
    const response = await fetch(`${base}/__admin/model-settings${sessionRoute ? "/session" : ""}`, {
      method: request.method, cache: "no-store", signal: AbortSignal.timeout(15000), body,
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json",
        "X-Stockanalysis-Model-Session": request.cookies.get(COOKIE)?.value || "" },
    });
    const data = await response.json();
    if (!response.ok) return error(typeof data.error === "string" ? data.error : "모델 설정 요청을 처리하지 못했습니다.", response.status);
    const result = NextResponse.json(sessionRoute ? { authorized: request.method === "POST" } : data, { headers: { "Cache-Control": "no-store" } });
    if (sessionRoute) {
      if (request.method === "POST" && (typeof data.session !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(data.session))) return error("관리자 세션을 만들지 못했습니다.", 503);
      result.cookies.set(COOKIE, request.method === "POST" ? data.session : "", {
        httpOnly: true, sameSite: "strict", secure: new URL(request.headers.get("origin")!).protocol === "https:",
        path: "/api/ai-model-settings", maxAge: request.method === "POST" ? SESSION_SECONDS : 0,
      });
    }
    return result;
  } catch { return error("모델 설정 서버에 연결하지 못했습니다.", 503); }
}
