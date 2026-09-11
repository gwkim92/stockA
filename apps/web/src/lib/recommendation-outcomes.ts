import { validId } from './evaluation-history';
export const OUTCOMES_PATH = '/performance/recommendations';
export const FILTER_KEYS = ['symbol','from_date','to_date','horizon','benchmark','alpha'] as const;
export type Filters = Record<typeof FILTER_KEYS[number], string>;
export type OutcomeQuery = Filters & { before: string; through: string };
export type Measurement = {
 outcome_id:string; recommendation_id:string; thesis_id:string|null; symbol:string; currency_code:string;
 strategy_name:string; market_code:string; recommendation_date:string; recommendation_action:string; recommendation_score:number;
 measurement_start_date:string; measurement_end_date:string; horizon_days:number; nominal_horizon:number|null;
 entry_price:number; exit_price:number; absolute_return_pct:number; benchmark_code:string|null; benchmark_return_pct:number|null;
 alpha_pct:number|null; max_drawdown_pct:number|null; outcome_label:string; recorded_at:string; source_run_id:string|null;
 evaluation_snapshot:{eval_run_id:string;snapshot_id:string;as_of_date:string|null;recorded_at:string}|null;
};
export type OutcomeReport = {
 rows:Measurement[]; filters:Filters; generated_at:string; benchmarks:(string|null)[];
 summary:{measurement_count:number;recommendation_count:number;symbol_count:number;missing_alpha_count:number;first_recommendation_date:string|null;last_recommendation_date:string|null};
 pagination:{limit:number;returned_count:number;through:string;has_more:boolean;next_cursor:string|null};
};
export type OutcomeResult = { report:OutcomeReport|null; query:OutcomeQuery; issue:'invalid'|'unavailable'|null };
export const emptyQuery = ():OutcomeQuery => ({symbol:'',from_date:'',to_date:'',horizon:'',benchmark:'',alpha:'',before:'',through:''});
const record = (v:unknown):Record<string,unknown> => v !== null && typeof v==='object' && !Array.isArray(v) ? v as Record<string,unknown> : {};
const number = (v:unknown):v is number => typeof v==='number' && Number.isFinite(v);
const integer = (v:unknown):v is number => number(v) && Number.isSafeInteger(v) && v>=0;
export function dateOnly(v:unknown):v is string {
 if(typeof v!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(v)||v.startsWith('0000')) return false;
 const d=new Date(v+'T00:00:00Z');return Number.isFinite(d.getTime()) && d.toISOString().slice(0,10)===v;
}
const watermark = (v:unknown):v is string => v==='0'||validId(v);
export const cursorValid = (v:unknown):v is string => typeof v==='string' && v.split(':').length===2 && dateOnly(v.split(':')[0]) && validId(v.split(':')[1]);
export function parseOutcomeQuery(raw:Record<string,unknown>):OutcomeQuery {
 const query=emptyQuery();
 for(const key of Object.keys(raw)) {
  if(!Object.hasOwn(query,key)||typeof raw[key]!=='string') throw Error('invalid query');
  query[key as keyof OutcomeQuery]=raw[key] as string;
 }
 query.symbol=query.symbol.toUpperCase();
 if(query.symbol&&!/^[A-Z0-9][A-Z0-9._-]{0,19}$/.test(query.symbol)) throw Error('invalid symbol');
 if((query.from_date&&!dateOnly(query.from_date))||(query.to_date&&!dateOnly(query.to_date))||(query.from_date&&query.to_date&&query.from_date>query.to_date)) throw Error('invalid dates');
 if(!['','30','90','180','365','other'].includes(query.horizon)||!['','positive','negative','zero','missing'].includes(query.alpha)) throw Error('invalid filter');
 if(query.benchmark&&!/^[A-Za-z0-9_^][A-Za-z0-9 ^&._/-]{0,63}$/.test(query.benchmark)) throw Error('invalid benchmark');
 if((query.before&&!cursorValid(query.before))||(query.through&&!watermark(query.through))) throw Error('invalid cursor');
 return query;
}
export function outcomeQueryString(query:Partial<OutcomeQuery>):string {
 const p=new URLSearchParams();for(const key of Object.keys(emptyQuery()) as (keyof OutcomeQuery)[]) if(query[key]) p.set(key,query[key]!);
 return p.toString();
}
export const outcomeHref = (query:Partial<OutcomeQuery>) => `${OUTCOMES_PATH}${outcomeQueryString(query)?'?'+outcomeQueryString(query):''}`;
export function percent(value:number|null, alpha=false):string {
 return value===null?'미측정':`${value>0?'+':''}${(value*100).toLocaleString('ko-KR',{minimumFractionDigits:2,maximumFractionDigits:2})}${alpha?'%p':'%'}`;
}
export function evaluationHref(snapshot:NonNullable<Measurement['evaluation_snapshot']>):string {
 const after=BigInt(snapshot.snapshot_id)-1n;
 return `/performance/evaluations/${snapshot.eval_run_id}${after>0n?'?after='+after:''}`;
}
export function parseOutcomeReport(raw:unknown, query:OutcomeQuery):OutcomeReport {
 const r=record(raw), p=record(r.pagination), s=record(r.summary), filters=record(r.filters);
 if(r.contract_version!=='recommendation-outcome-explorer-v1'||r.source!=='live'||r.read_only!==true||r.horizon_tolerance_days!==7||r.record_basis!=='stored_measurements_with_current_recommendation_links') throw Error('invalid report');
 if(FILTER_KEYS.some(k=>filters[k]!==query[k])||typeof r.generated_at!=='string'||!Number.isFinite(Date.parse(r.generated_at))) throw Error('wrong scope');
 if(!watermark(p.through)||(query.through&&p.through!==query.through)||p.limit!==25||typeof p.has_more!=='boolean'||(p.next_cursor!==null&&!cursorValid(p.next_cursor))) throw Error('invalid pagination');
 if(p.has_more!==(p.next_cursor!==null)||!Array.isArray(r.rows)||r.rows.length>25||p.returned_count!==r.rows.length) throw Error('invalid page');
 if(!Array.isArray(r.benchmarks)||r.benchmarks.some(v=>v!==null&&typeof v!=='string')) throw Error('invalid benchmarks');
 for(const k of ['measurement_count','recommendation_count','symbol_count','missing_alpha_count']) if(!integer(s[k])) throw Error('invalid counts');
 if((s.measurement_count as number)<r.rows.length||(s.recommendation_count as number)>(s.measurement_count as number)||(s.symbol_count as number)>(s.recommendation_count as number)||(s.missing_alpha_count as number)>(s.measurement_count as number)) throw Error('invalid counts');
 for(const k of ['first_recommendation_date','last_recommendation_date']) if(s[k]!==null&&!dateOnly(s[k])) throw Error('invalid range');
 let previous=query.before?query.before.split(':'):null;
 const seen=new Set<string>();
 for(const value of r.rows) {
  const row=record(value);
  if(!validId(row.outcome_id)||!validId(row.recommendation_id)||(row.thesis_id!==null&&!validId(row.thesis_id))||(row.source_run_id!==null&&!validId(row.source_run_id))||seen.has(row.outcome_id)||BigInt(row.outcome_id)>BigInt(p.through)) throw Error('invalid identity');
  seen.add(row.outcome_id);
  for(const k of ['symbol','currency_code','strategy_name','market_code','recommendation_action','outcome_label','recorded_at']) if(typeof row[k]!=='string'||!row[k]) throw Error('missing context');
  if(!/^[A-Za-z0-9][A-Za-z0-9._-]{0,19}$/.test(row.symbol as string)||!dateOnly(row.recommendation_date)||!dateOnly(row.measurement_start_date)||!dateOnly(row.measurement_end_date)||row.measurement_start_date>row.measurement_end_date||!integer(row.horizon_days)) throw Error('invalid dates');
  for(const k of ['recommendation_score','entry_price','exit_price','absolute_return_pct']) if(!number(row[k])) throw Error('invalid metric');
  for(const k of ['benchmark_return_pct','alpha_pct','max_drawdown_pct']) if(row[k]!==null&&!number(row[k])) throw Error('invalid metric');
  if(row.benchmark_code!==null&&typeof row.benchmark_code!=='string') throw Error('invalid benchmark');
  if(row.nominal_horizon!==null&&![30,90,180,365].includes(row.nominal_horizon as number)) throw Error('invalid horizon');
  if(previous&&(row.measurement_end_date>previous[0]||(row.measurement_end_date===previous[0]&&BigInt(row.outcome_id)>=BigInt(previous[1])))) throw Error('invalid order');
  previous=[row.measurement_end_date,row.outcome_id];
  if(row.evaluation_snapshot!==null) {const e=record(row.evaluation_snapshot);if(!validId(e.eval_run_id)||!validId(e.snapshot_id)||(e.as_of_date!==null&&!dateOnly(e.as_of_date))||typeof e.recorded_at!=='string') throw Error('invalid snapshot');}
 }
 if(p.has_more&&(r.rows.length!==25||!previous||p.next_cursor!==previous.join(':'))) throw Error('invalid continuation');
 return r as unknown as OutcomeReport;
}
export async function loadRecommendationOutcomes(raw:Record<string,unknown>, options:{fetcher?:typeof fetch;timeoutMs?:number}={}):Promise<OutcomeResult> {
 let query:OutcomeQuery;try {query=parseOutcomeQuery(raw);} catch {return {report:null,query:emptyQuery(),issue:'invalid'};}
 const controller=new AbortController();let timer:ReturnType<typeof setTimeout>|undefined;
 try {
  const base=(process.env.STOCKANALYSIS_FRONTEND_API_BASE_URL??'http://127.0.0.1:8765').replace(/\/$/,'');
  const token=process.env.STOCKANALYSIS_FRONTEND_API_READ_TOKEN;
  const read=async()=>{
   const suffix=outcomeQueryString(query);
   const response=await(options.fetcher??fetch)(`${base}/api/recommendation-outcomes?limit=25${suffix?'&'+suffix:''}`,{method:'GET',cache:'no-store',redirect:'error',signal:controller.signal,headers:{Accept:'application/json',...(token?{Authorization:`Bearer ${token}`}:{})}});
   if(!response.ok) throw Error('unavailable');return parseOutcomeReport(await response.json(),query);
  };
  const deadline=new Promise<never>((_,reject)=>{timer=setTimeout(()=>{controller.abort();reject(Error('timeout'));},options.timeoutMs??8000);});
  return {report:await Promise.race([read(),deadline]),query,issue:null};
 } catch {return {report:null,query,issue:'unavailable'};}
 finally {clearTimeout(timer);}
}
