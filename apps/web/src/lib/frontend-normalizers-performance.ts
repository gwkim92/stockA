import { ensureRecord, type MutableRecord, withDefault } from "./frontend-normalizer-utils";

export function normalizePerformanceOutcomesPayload(data: MutableRecord) {
  const summary = ensureRecord(data, "summary");
  withDefault(data, "quality_evaluation", {
    status: "not_available",
    sample_size_status: "not_available",
    score_outcome_alignment: "not_available",
    review_outcome_mismatch_count: 0,
    measured_recommendation_count: summary.measured_recommendation_count ?? 0,
    measured_thesis_count: summary.measured_thesis_count ?? 0,
    average_alpha: summary.average_alpha ?? null,
    hit_rate: summary.hit_rate ?? null,
    high_score_recommendation_count: 0,
    high_score_average_alpha: null,
    coverage_exclusion_count: summary.excluded_position_count ?? 0,
    checks: [],
  });
}
