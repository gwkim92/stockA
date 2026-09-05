import type { RecommendationListData } from "./types";
export type ExplorerRow = RecommendationListData["recommendations"][number];
export type ExplorerFilter = "all" | "linked" | "limited";
export function sourceLimited(row: ExplorerRow): boolean {
  return row.evidence_quality.source_blocker?.blocked === true || row.evidence_quality.status === "source_blocked" || row.evidence.quality_status === "blocked";
}
/** Filtering only: preserve incoming order, scores, evidence and all permission fields. */
export function filterRecommendations(rows: readonly ExplorerRow[], query: string, filter: ExplorerFilter): readonly ExplorerRow[] {
  const search = query.trim().toLocaleLowerCase();
  return rows.filter(row => (!search || `${row.symbol} ${row.name}`.toLocaleLowerCase().includes(search))
    && (filter === "all" || (filter === "limited" ? sourceLimited(row) : Boolean(row.linked_thesis_id) && !sourceLimited(row))));
}
export function researchScore(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1 ? `${value.toFixed(2)} / 1` : "미확인";
}
