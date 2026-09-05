import { parseReviewReport, REVIEW_PORTFOLIO, selectedDate, type ReviewKind, type ReviewReport } from "./review-workspace-model";
export type ReviewResult = { report: ReviewReport | null; issue: "date" | "http" | "network" | "invalid" | "timeout" | null; requestedDate: string; today: string };
export async function loadReviewReport(kind: ReviewKind, value?: unknown, options: { now?: Date; timeoutMs?: number; fetcher?: typeof fetch } = {}): Promise<ReviewResult> {
  const today = (options.now ?? new Date()).toISOString().slice(0, 10), date = selectedDate(value, today);
  if (!date) return { report: null, issue: "date", requestedDate: today, today };
  const target = encodeURIComponent(REVIEW_PORTFOLIO);
  const path = kind === "portfolio" ? `/api/portfolio/${target}/coverage?asOfDate=${date}` : `/api/performance/${target}/outcomes?measurementEndDate=${date}`;
  const base = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? "http://127.0.0.1:8765").replace(/\/$/, "");
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let issue: ReviewResult["issue"] = "network";
  const deadline = new Promise<never>((_, reject) => { timer = setTimeout(() => { issue = "timeout"; controller.abort(); reject(new Error("deadline")); }, options.timeoutMs ?? 5000); });
  try {
    const read = async () => {
      const response = await (options.fetcher ?? fetch)(`${base}${path}`, { method: "GET", cache: "no-store", redirect: "error", signal: controller.signal,
        headers: { Accept: "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
      if (!response.ok) { issue = "http"; throw new Error("request failed"); }
      try { return parseReviewReport(kind, await response.json()); }
      catch { if (issue !== "timeout") issue = "invalid"; throw new Error("invalid response"); }
    };
    return { report: await Promise.race([read(), deadline]), issue: null, requestedDate: date, today };
  } catch { return { report: null, issue, requestedDate: date, today }; }
  finally { clearTimeout(timer); }
}
