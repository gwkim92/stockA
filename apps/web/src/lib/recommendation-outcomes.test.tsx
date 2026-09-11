import { afterEach, describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { RecommendationOutcomes } from '@/components/review/RecommendationOutcomes';
import { emptyQuery, evaluationHref, loadRecommendationOutcomes, outcomeHref, parseOutcomeQuery, parseOutcomeReport, percent } from './recommendation-outcomes';
const measurement = (id = '1') => ({
  outcome_id:id, recommendation_id:'7', thesis_id:'2', symbol:'AAPL', currency_code:'USD', strategy_name:'long_term_core', market_code:'US', recommendation_date:'2026-06-01',
  recommendation_action:'watch', recommendation_score:0, measurement_start_date:'2026-06-01', measurement_end_date:'2026-06-29', horizon_days:28, nominal_horizon:30,
  entry_price:100, exit_price:100, absolute_return_pct:0, benchmark_code:null, benchmark_return_pct:null, alpha_pct:null, max_drawdown_pct:0, outcome_label:'flat',
  recorded_at:'2026-06-30T00:00:00Z', source_run_id:null, evaluation_snapshot:{eval_run_id:'8',snapshot_id:'9223372036854775807',as_of_date:'2026-09-10',recorded_at:'2026-09-10T00:00:00Z'},
});
const payload = () => ({
  contract_version:'recommendation-outcome-explorer-v1', source:'live', read_only:true, horizon_tolerance_days:7, record_basis:'stored_measurements_with_current_recommendation_links',
  generated_at:'2026-09-10T00:00:00Z', filters:emptyQuery(), benchmarks:['SPY',null],
  summary:{measurement_count:40,recommendation_count:20,symbol_count:3,missing_alpha_count:1,first_recommendation_date:'2026-06-01',last_recommendation_date:'2026-06-02'},
  rows:[measurement()], pagination:{limit:25,returned_count:1,through:'50',has_more:false,next_cursor:null as string|null},
});
afterEach(()=>vi.unstubAllEnvs());
describe('recommendation outcomes',()=>{
  it('normalizes filter URLs and rejects invalid input before fetching',async()=>{
    expect(parseOutcomeQuery({symbol:'aapl',benchmark:'S&P 500'}).symbol).toBe('AAPL');
    expect(outcomeHref({symbol:'AAPL',benchmark:'S&P 500'})).toBe('/performance/recommendations?symbol=AAPL&benchmark=S%26P+500');
    const fetcher=vi.fn();
    for(const raw of [{symbol:['AAPL','SPY']},{from_date:'2026-02-30'},{from_date:'0000-01-01'},{constructor:'bad'},{from_date:'2026-08-01',to_date:'2026-07-01'},{horizon:'31'},{before:'2026-09-10:01'},{through:'9223372036854775808'},{bad:'1'}]) expect((await loadRecommendationOutcomes(raw,{fetcher})).issue).toBe('invalid');
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('preserves missing and zero metrics, exact snapshot IDs and full-scope counts',()=>{
    const report=parseOutcomeReport(payload(),emptyQuery());
    expect(report.summary.measurement_count).toBe(40);expect(report.rows[0].absolute_return_pct).toBe(0);
    expect(percent(0)).toBe('0.00%');expect(percent(null)).toBe('미측정');expect(percent(.05,true)).toBe('+5.00%p');
    expect(evaluationHref(report.rows[0].evaluation_snapshot!)).toBe('/performance/evaluations/8?after=9223372036854775806');
    const html=renderToStaticMarkup(<RecommendationOutcomes result={{report,query:emptyQuery(),issue:null}}/>);
    for(const text of ['실제 28일 관찰','0.00%','미측정','/recommendations/recommendation-7','/theses/thesis-2','평가 실행 시점']) expect(html).toContain(text);
    expect(html).not.toContain('평균 수익률');
  });
  it('checks page order, cursor, watermark, contract and echoed filters',()=>{
    const report=payload();report.rows=Array.from({length:25},(_,i)=>measurement(String(50-i)));
    report.pagination={limit:25,returned_count:25,through:'50',has_more:true,next_cursor:'2026-06-29:26'};
    expect(parseOutcomeReport(report,emptyQuery()).pagination.has_more).toBe(true);
    for(const raw of [{...report,source:'fixture'},{...report,filters:{...emptyQuery(),symbol:'SPY'}},{...report,rows:[report.rows[0],report.rows[0]]},{...report,pagination:{...report.pagination,next_cursor:'2026-06-29:27'}},{...report,pagination:{...report.pagination,through:'49'}},{...report,rows:[{...report.rows[0],alpha_pct:'0'},...report.rows.slice(1)]}]) expect(()=>parseOutcomeReport(raw,emptyQuery())).toThrow();
    expect(()=>parseOutcomeReport(report,{...emptyQuery(),before:'2026-06-29:49'})).toThrow();expect(()=>parseOutcomeReport(report,{...emptyQuery(),through:'40'})).toThrow();
  });
  it('uses authenticated no-store reads and does not expose tokens or failures',async()=>{
    vi.stubEnv('STOCKANALYSIS_FRONTEND_API_READ_TOKEN','only-on-server');
    const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify(payload())));
    const result=await loadRecommendationOutcomes({},{fetcher});expect(result.issue).toBeNull();
    expect(fetcher.mock.calls[0][0]).toMatch(/recommendation-outcomes\?limit=25$/);
    expect(fetcher.mock.calls[0][1]).toMatchObject({method:'GET',cache:'no-store',redirect:'error',headers:{Authorization:'Bearer only-on-server'}});
    expect(JSON.stringify(result)).not.toContain('only-on-server');
    for(const status of [401,404,503]) {const failed=await loadRecommendationOutcomes({},{fetcher:vi.fn().mockResolvedValue(new Response('private SQL',{status}))});expect(failed).toMatchObject({report:null,issue:'unavailable'});expect(JSON.stringify(failed)).not.toContain('private SQL');}
    expect((await loadRecommendationOutcomes({},{fetcher:vi.fn().mockReturnValue(new Promise(()=>{})),timeoutMs:10})).issue).toBe('unavailable');
  });
  it('shows empty results separately from failed reads',()=>{
    const raw=payload();raw.rows=[];raw.summary={measurement_count:0,recommendation_count:0,symbol_count:0,missing_alpha_count:0,first_recommendation_date:'2026-06-01',last_recommendation_date:'2026-06-01'};raw.pagination.returned_count=0;
    const report=parseOutcomeReport(raw,emptyQuery());
    expect(renderToStaticMarkup(<RecommendationOutcomes result={{report,query:emptyQuery(),issue:null}}/>)).toContain('조건에 맞는 저장 성과가 없습니다');
    const failed=renderToStaticMarkup(<RecommendationOutcomes result={{report:null,query:emptyQuery(),issue:'unavailable'}}/>);
    expect(failed).toContain('성과 자료를 불러오지 못했습니다');expect(failed).not.toContain('저장된 측정');
  });
});
