// @vitest-environment node
import { describe, expect, it } from 'vitest';
import { outcome, type ReviewReport } from './review-workspace-model';
import { cohortStats, recommendationQualityAudit } from './recommendation-quality-model';

const report = (patch: Record<string, unknown> = {}): ReviewReport => ({
  kind: 'performance', partial: false, rows: [
    { outcome_id:'o1',symbol:'AAPL',recommendation_id:'r1',thesis_id:'t1',recommendation:'accumulate',horizon_days:90,alpha:0.06,absolute_return:0.1,benchmark_return:0.04,security_contribution_bps:30 },
    { outcome_id:'o2',symbol:'SPY',recommendation_id:'r2',thesis_id:null,recommendation:'monitor',horizon_days:365,alpha:-0.02,absolute_return:0.02,benchmark_return:0.04,security_contribution_bps:-20 },
    { outcome_id:'o3',symbol:'EROK',recommendation_id:null,thesis_id:null,recommendation:'monitor',horizon_days:null,alpha:null,absolute_return:null,benchmark_return:null,security_contribution_bps:null },
  ],
  raw: {
    portfolio_name:'Long Term Paper', benchmark_code:'SPY',
    summary:{ measured_recommendation_count:2, average_alpha:0.02, hit_rate:0.5 },
    quality_evaluation:{ status:'insufficient_sample', sample_size_status:'insufficient_sample' },
    coverage_exclusions:[{symbol:'BABA',weight:0.03,reason:'missing_thesis',required_action:'needs_thesis_review'}],
    quality_gates:[{gate:'coverage_ready',status:'blocked',reason:'missing thesis'}],
    attribution_components:[{component_type:'security_selection',label:'AAPL selection',symbol:'AAPL',theme_key:'AI',alpha:0.06,contribution_bps:30}],
    ...patch,
  },
});
const outcomes = (value: ReviewReport) => value.rows.map(outcome);

describe('recommendation quality audit', () => {
  it('derives measurable rows without rewriting report-level summary', () => {
    const source=report(), before=JSON.stringify(source), audit=recommendationQualityAudit(source,outcomes(source));
    expect(audit.derived).toMatchObject({received:3,measured:2,unmeasured:1,averageAlpha:0.02,hitRate:0.5,recommendationLinked:2,thesisLinked:1,benchmarkMeasured:2});
    expect(audit.mismatchCount).toBe(0);expect(JSON.stringify(source)).toBe(before);
  });
  it('reports summary disagreement instead of silently correcting it', () => {
    const source=report({summary:{measured_recommendation_count:3,average_alpha:0.9,hit_rate:1}}), audit=recommendationQualityAudit(source,outcomes(source));
    expect(audit.checks.map(check=>check.status)).toEqual(['mismatch','mismatch','mismatch']);expect(audit.mismatchCount).toBe(3);
  });
  it('uses unavailable instead of false zero when no row is measurable', () => {
    const source=report({summary:{measured_recommendation_count:0}});source.rows=source.rows.map(row=>({...row,alpha:null,horizon_days:null,benchmark_return:null}));
    const audit=recommendationQualityAudit(source,outcomes(source));
    expect(audit.derived.measured).toBe(0);expect(audit.derived.averageAlpha).toBeNull();expect(audit.derived.hitRate).toBeNull();
    expect(audit.checks.find(check=>check.key==='alpha')?.status).toBe('unavailable');expect(audit.checks.find(check=>check.key==='hit')?.status).toBe('unavailable');
  });
  it('keeps observation horizons separate', () => {
    const source=report(), audit=recommendationQualityAudit(source,outcomes(source));
    expect(audit.horizonCohorts.map(row=>[row.label,row.measured,row.averageAlpha])).toEqual([['90일',1,0.06],['365일',1,-0.02]]);
  });
  it('keeps recommendation actions as cohorts and preserves unmeasured totals', () => {
    const source=report(), audit=recommendationQualityAudit(source,outcomes(source));
    const monitor=audit.actionCohorts.find(row=>row.label==='monitor')!;
    expect(monitor.total).toBe(2);expect(monitor.measured).toBe(1);expect(monitor.averageAlpha).toBe(-0.02);
  });
  it('preserves exclusions, quality gates and attribution lenses without adding them together', () => {
    const source=report(), audit=recommendationQualityAudit(source,outcomes(source));
    expect(audit.exclusions).toEqual([{symbol:'BABA',weight:0.03,reason:'missing_thesis',action:'needs_thesis_review'}]);
    expect(audit.gates[0]).toEqual({gate:'coverage_ready',status:'blocked',reason:'missing thesis'});
    expect(audit.lenses[0]).toMatchObject({type:'security_selection',label:'AAPL selection',contributionBps:30,alpha:0.06,symbol:'AAPL',theme:'AI'});
  });
  it('degrades malformed optional collections to empty audit sections', () => {
    const source=report({coverage_exclusions:'bad',quality_gates:{bad:true},attribution_components:null,quality_evaluation:'bad'}), audit=recommendationQualityAudit(source,outcomes(source));
    expect(audit.exclusions).toEqual([]);expect(audit.gates).toEqual([]);expect(audit.lenses).toEqual([]);expect(audit.qualityStatus).toBe('미확인');
  });
  it('cohortStats never reports 0% as a measured hit rate for an empty cohort', () => {
    expect(cohortStats([], 'none', '없음')).toEqual({key:'none',label:'없음',measured:0,total:0,averageAlpha:null,hitRate:null});
  });
});
