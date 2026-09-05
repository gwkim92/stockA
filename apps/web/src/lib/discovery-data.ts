import { parseDiscovery, type DiscoveryData, type DiscoveryKind } from "./discovery-model";
export type DiscoveryResult = { data: DiscoveryData | null; issue: "timeout" | "http" | "invalid" | "network" | null; requestedDate: string };
/** A response-body deadline, authenticated read only, and no fixture-on-error fallback. */
export async function loadDiscovery(kind: DiscoveryKind, options: { now?: Date; timeoutMs?: number; fetcher?: typeof fetch } = {}): Promise<DiscoveryResult> {
  const requestedDate = (options.now ?? new Date()).toISOString().slice(0, 10);
  const path = kind === "stocks" ? "/api/stocks" : `/api/${kind === "cycles" ? "cycles" : "market-map"}?asOfDate=${requestedDate}`;
  const base = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? "http://127.0.0.1:8765").replace(/\/$/, "");
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let issue: DiscoveryResult["issue"] = "network";
  const deadline = new Promise<never>((_, reject) => { timer = setTimeout(() => { issue = "timeout"; controller.abort(); reject(new Error("deadline")); }, options.timeoutMs ?? 5000); });
  try {
    const read = async () => {
      const response = await (options.fetcher ?? fetch)(`${base}${path}`, { method: "GET", cache: "no-store", redirect: "error", signal: controller.signal,
        headers: { Accept: "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
      if (!response.ok) { issue = "http"; throw new Error("http"); }
      try { return parseDiscovery(kind, await response.json()); }
      catch { if (issue !== "timeout") issue = "invalid"; throw new Error("payload"); }
    };
    return { data: await Promise.race([read(), deadline]), issue: null, requestedDate };
  } catch { return { data: null, issue, requestedDate }; }
  finally { clearTimeout(timer); }
}
