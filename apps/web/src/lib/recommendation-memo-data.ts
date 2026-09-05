import { getThesisDetail } from "./frontend-api";
import type { RecommendationDetailData, ThesisDetailData, ApiResponse } from "./types";
import { thesisMatchesRecommendation, type MemoThesisResult } from "./recommendation-memo-model";

/** Optional enrichment. A failed thesis must not erase a usable recommendation. */
export async function loadRecommendationThesis(
  data: RecommendationDetailData,
  options: { timeoutMs?: number; read?: (id: string, options: { signal: AbortSignal }) => Promise<ApiResponse<ThesisDetailData>> } = {},
): Promise<MemoThesisResult> {
  if (typeof data.linked_thesis_id !== "string" || !data.linked_thesis_id.trim()) return { status: "not_linked", data: null };
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let timedOut = false;
  const deadline = new Promise<never>((_, reject) => {
    timer = setTimeout(() => { timedOut = true; controller.abort(); reject(new Error("thesis deadline")); }, options.timeoutMs ?? 3_000);
  });
  try {
    const response = await Promise.race([(options.read ?? getThesisDetail)(data.linked_thesis_id, { signal: controller.signal }), deadline]);
    return thesisMatchesRecommendation(data, response.data)
      ? { status: "available", data: response.data } : { status: "mismatch", data: null };
  } catch {
    return { status: timedOut ? "timeout" : "unavailable", data: null };
  } finally { clearTimeout(timer); }
}
