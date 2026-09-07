/** Read-only audit projections over the stored performance report. */
import { count, fraction, list, number, record, words, type Outcome, type ReviewReport } from './review-workspace-model';

export type AuditCheck = { key: string; label: string; status: 'match' | 'mismatch' | 'unavailable'; stored: number | null; derived: number | null };
export type QualityCohort = { key: string; label: string; measured: number; total: number; averageAlpha: number | null; hitRate: number | null };
export type QualityGate = { gate: string; status: string; reason: string };
export type CoverageExclusion = { symbol: string; weight: number | null; reason: string; action: string };
export type AttributionLens = { type: string; label: string; contributionBps: number | null; alpha: number | null; symbol: string | null; theme: string | null };

const mean = (values: number[]): number | null => values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
const near = (a: number | null, b: number | null, epsilon = 1e-9) => a !== null && b !== null && Math.abs(a - b) <= epsilon;
const measurable = (row: Outcome) => row.alpha !== null && row.horizon !== null && row.horizon > 0;

export function cohortStats(rows: readonly Outcome[], key: string, label: string): QualityCohort {
  const eligible = rows.filter(measurable), alphas = eligible.map(row => row.alpha!).filter(Number.isFinite);
  return {
    key, label, total: rows.length, measured: eligible.length,
    averageAlpha: mean(alphas), hitRate: eligible.length ? eligible.filter(row => row.alpha! > 0).length / eligible.length : null,
  };
}

export function recommendationQualityAudit(report: ReviewReport, outcomes: readonly Outcome[]) {
  const summary = record(report.raw.summary);
  const eligible = outcomes.filter(measurable), measuredAlpha = eligible.map(row => row.alpha!);
  const derived = {
    received: outcomes.length,
    measured: eligible.length,
    unmeasured: outcomes.length - eligible.length,
    averageAlpha: mean(measuredAlpha),
    hitRate: eligible.length ? eligible.filter(row => row.alpha! > 0).length / eligible.length : null,
    recommendationLinked: eligible.filter(row => row.recommendationId !== null).length,
    thesisLinked: eligible.filter(row => row.thesisId !== null).length,
    benchmarkMeasured: eligible.filter(row => row.benchmark !== null).length,
  };
  const stored = {
    measured: count(summary.measured_recommendation_count),
    averageAlpha: number(summary.average_alpha),
    hitRate: fraction(summary.hit_rate),
  };
  const checks: AuditCheck[] = [
    { key: 'measured', label: '측정 추천 수', status: stored.measured === null ? 'unavailable' : stored.measured === derived.measured ? 'match' : 'mismatch', stored: stored.measured, derived: derived.measured },
    { key: 'alpha', label: '평균 초과수익', status: stored.averageAlpha === null || derived.averageAlpha === null ? 'unavailable' : near(stored.averageAlpha, derived.averageAlpha) ? 'match' : 'mismatch', stored: stored.averageAlpha, derived: derived.averageAlpha },
    { key: 'hit', label: '적중률', status: stored.hitRate === null || derived.hitRate === null ? 'unavailable' : near(stored.hitRate, derived.hitRate) ? 'match' : 'mismatch', stored: stored.hitRate, derived: derived.hitRate },
  ];

  const horizons = [...new Set(outcomes.map(row => row.horizon).filter((value): value is number => value !== null))].sort((a,b)=>a-b);
  const horizonCohorts = horizons.map(horizon => cohortStats(outcomes.filter(row => row.horizon === horizon), `horizon-${horizon}`, `${horizon}일`));
  const actions = [...new Set(outcomes.map(row => row.action).filter(Boolean))].sort();
  const actionCohorts = actions.map(action => cohortStats(outcomes.filter(row => row.action === action), `action-${action}`, action));

  const exclusions: CoverageExclusion[] = (list(report.raw.coverage_exclusions) ?? []).map(row => ({
    symbol: words(row.symbol), weight: fraction(row.weight), reason: words(row.reason), action: words(row.required_action),
  }));
  const gates: QualityGate[] = (list(report.raw.quality_gates) ?? []).map(row => ({ gate: words(row.gate), status: words(row.status), reason: words(row.reason) }));
  const lenses: AttributionLens[] = (list(report.raw.attribution_components) ?? []).map(row => ({
    type: words(row.component_type), label: words(row.label), contributionBps: number(row.contribution_bps), alpha: number(row.alpha),
    symbol: words(row.symbol, '') || null, theme: words(row.theme_key, '') || null,
  }));
  const quality = record(report.raw.quality_evaluation);
  return {
    derived, stored, checks, horizonCohorts, actionCohorts, exclusions, gates, lenses,
    qualityStatus: words(quality.status), sampleStatus: words(quality.sample_size_status),
    mismatchCount: checks.filter(check => check.status === 'mismatch').length,
  };
}
