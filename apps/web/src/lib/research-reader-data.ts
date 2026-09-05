import { identifier, parseSource, parseThesis, type ReaderKind, type SourceReaderData, type ThesisReaderData } from "./research-reader-model";
export type ReaderIssue = "identifier" | "not-found" | "http" | "network" | "invalid" | "timeout";
export type ReaderResult<T> = { data: T | null; issue: ReaderIssue | null; today: string };
type Options = { now?: Date; fetcher?: typeof fetch; timeoutMs?: number };
export function loadReader(kind: "thesis", requested: string, options?: Options): Promise<ReaderResult<ThesisReaderData>>;
export function loadReader(kind: "source", requested: string, options?: Options): Promise<ReaderResult<SourceReaderData>>;
export async function loadReader(kind: ReaderKind, requested: string, options: Options = {}): Promise<ReaderResult<ThesisReaderData | SourceReaderData>> {
  const today = (options.now ?? new Date()).toISOString().slice(0, 10);
  if (!identifier(requested)) return { data: null, issue: "identifier", today };
  const base = (process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL ?? "http://127.0.0.1:8765").replace(/\/$/, "");
  const token = process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let issue: ReaderIssue = "network";
  const deadline = new Promise<never>((_, reject) => { timer = setTimeout(() => { issue = "timeout"; controller.abort(); reject(new Error("deadline")); }, options.timeoutMs ?? 5000); });
  try {
    const read = async () => {
      const resource = kind === "thesis" ? "theses" : "source-documents";
      const response = await (options.fetcher ?? fetch)(`${base}/api/${resource}/${encodeURIComponent(requested)}`, {
        method: "GET", cache: "no-store", redirect: "error", signal: controller.signal,
        headers: { Accept: "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      });
      if (!response.ok) { issue = response.status === 404 ? "not-found" : "http"; throw new Error("request failed"); }
      try { const payload: unknown = await response.json(); return kind === "thesis" ? parseThesis(payload, requested) : parseSource(payload, requested); }
      catch { if (issue !== "timeout") issue = "invalid"; throw new Error("invalid reader payload"); }
    };
    return { data: await Promise.race([read(), deadline]), issue: null, today };
  } catch { return { data: null, issue, today }; }
  finally { clearTimeout(timer); }
}
