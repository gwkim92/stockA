// Actual browser checks against the production Next build and synthetic read API.
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import assert from 'node:assert/strict';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'apps/web/package.json'));
const { chromium, expect } = require('@playwright/test');
const { default: AxeBuilder } = require('@axe-core/playwright');
const out = path.join(root, 'artifacts/evaluation-history/browser');
await mkdir(out, { recursive: true });
let mode = 'healthy'; const requests = [], captures = [];
const run = (id='9', state='recorded', count=2) => ({eval_run_id:id, as_of_date:'2026-01-15', created_at:'2026-01-16T09:00:00Z',horizon_days:30,snapshot_count:count,snapshot_state:state});
const snapshot = (id='1') => ({snapshot_id:id,source_recommendation_id:'9223372036854775807',primary_symbol:id==='1'?'AAPL':'MSFT',recommendation_action:'watch',recommendation_total_score:0,snapshot_json:{recommendation:{action:'watch',total_score:0},thesis:{summary:'매출 성장과 현금흐름을 근거로 수익성 회복을 관찰합니다. 새로운 공시가 이 판단을 뒷받침하는지 확인합니다.',invalidation_conditions:['수요 감소가 두 분기 연속 이어지는 경우']},selected_outcome:{alpha_pct:null,horizon_days:30,measurement_end_date:'2026-01-10'}}});
const history = (detail, after) => ({contract_version:'recommendation-eval-history-v1',source:'live',read_only:true,history_basis:'evaluation_time_snapshot_not_recommendation_creation_time',...(detail?{run:run('9',mode==='legacy'?'legacy_unavailable':mode==='count-mismatch'?'count_mismatch':'recorded',mode==='legacy'?0:2),snapshots:mode==='legacy'?[]:[snapshot(after?'2':'1')]}:{runs:mode==='empty'?[]:after?[run('8','recorded_empty',0)]:[run()]}),pagination:{next_cursor:mode==='empty'||mode==='legacy'||after?null:'1',has_more:!['empty','legacy'].includes(mode)&&!after,returned_count:mode==='empty'||mode==='legacy'?0:1}});
const fixture = JSON.parse(await readFile(path.join(root,'docs/api/frontend/examples/performance-outcomes.json'),'utf8'));
const api = createServer((req,res)=>{
  const url=new URL(req.url,'http://127.0.0.1');
  const send=(status,value)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
  if(url.pathname==='/__health')return send(200,{});
  requests.push({path:url.pathname,method:req.method});
  if(req.method!=='GET'||req.headers.authorization!=='Bearer eval-history-test')return send(401,{});
  if(url.pathname.includes('/outcomes'))return send(200,fixture);
  if(mode==='unavailable')return send(503,{});
  if(mode==='missing')return send(404,{});
  const detail=url.pathname.startsWith('/api/recommendation-evaluation-comparisons/');
  const h=history(detail,url.searchParams.get(detail?'after':'before'));
  if(!detail)return send(200,h);
  const state=mode==='corrupt'?'untrusted_history':mode==='source-unavailable'?'unavailable':mode==='source-missing'?'source_missing':mode==='unchanged'?'unchanged':'changed';
  const comparisons=h.snapshots.map(s=>({snapshot_id:s.snapshot_id,integrity:mode==='corrupt'?'mismatch':'verified',status:state,changes:state==='changed'?[{field:'recommendation.action',recorded:'watch',current:'buy'},{field:'thesis.summary',recorded:s.snapshot_json.thesis.summary,current:'새 공시에서 수익성 회복을 확인했습니다. 다음 분기에도 개선 흐름이 이어지는지 검토합니다.'}]:[],later_outcome:state==='changed'?{alpha_pct:0,benchmark_code:'SPY',measurement_start_date:'2026-01-01',measurement_end_date:'2026-02-01',horizon_days:30}:null}));
  if(mode==='malformed')h.run.eval_run_id='123';
  return send(200,{contract_version:'recommendation-eval-comparison-v1',read_only:true,history:h,comparisons,compared_at:'2026-09-08T05:00:00Z'});
});
await new Promise(resolve=>api.listen(18779,'127.0.0.1',resolve));
const child=spawn(process.execPath,[require.resolve('next/dist/bin/next'),'start','-H','127.0.0.1','-p','13019'],{cwd:path.join(root,'apps/web'),env:{...process.env,STOCKANALYSIS_FRONTEND_API_BASE_URL:'http://127.0.0.1:18779',STOCKANALYSIS_FRONTEND_API_READ_TOKEN:'eval-history-test',NEXT_TELEMETRY_DISABLED:'1'},stdio:['ignore','pipe','pipe']});
let log='';child.stdout.on('data',d=>log+=d);child.stderr.on('data',d=>log+=d);
let browser;
try {
  for(let i=0;i<80;i++){try{if((await fetch('http://127.0.0.1:13019/performance/evaluations')).ok)break;}catch{}if(i===79)throw Error('Next startup failed');await new Promise(r=>setTimeout(r,250));}
  browser=await chromium.launch({headless:true});
  for(const [name,width,height] of [['desktop',1440,1000],['tablet',768,900],['mobile',390,844]]){
    const context=await browser.newContext({viewport:{width,height}});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
    const capture=async(id)=>{
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true,`${name}/${id} overflow`);
      const violations=(await new AxeBuilder({page}).analyze()).violations;assert.deepEqual(violations,[],`${name}/${id} accessibility`);
      await page.evaluate(()=>{ if(document.activeElement instanceof HTMLElement)document.activeElement.blur(); window.scrollTo({top:0,left:0,behavior:'instant'}); });
      await page.waitForFunction(()=>window.scrollY===0);
      const file=path.join(out,`${name}-${id}.png`);await page.screenshot({path:file,fullPage:true,animations:'disabled'});captures.push({viewport:name,state:id,path:file});
      if(['performance-reference','list'].includes(id))await page.screenshot({path:path.join(out,`${name}-${id}-viewport.png`),animations:'disabled'});
      assert.deepEqual(errors,[]);
    };
    mode='healthy';await page.goto('http://127.0.0.1:13019/performance');await expect(page.getByRole('heading',{name:'판단 성과',exact:true,level:1})).toBeVisible();await capture('performance-reference');
    await page.getByRole('link',{name:'평가 이력',exact:true}).click();await expect(page.getByRole('heading',{name:'저장된 평가'})).toBeVisible();await capture('list');
    await page.getByRole('link',{name:'이전 평가 더 보기'}).click();await expect(page.getByText('평가 대상 없음',{exact:true})).toBeVisible();await capture('list-next');
    await page.getByRole('link',{name:'처음 페이지'}).click();await page.getByRole('link',{name:'2026-01-15 평가',exact:true}).click();await expect(page.getByRole('heading',{name:'AAPL',exact:true})).toBeVisible();await expect(page.getByText('0.00%p',{exact:true})).toBeVisible();await capture('detail');
    await page.getByText('기록 범위와 원문 확인',{exact:true}).click();await expect(page.getByRole('link',{name:'현재 추천 상세 보기'})).toHaveAttribute('href','/recommendations/recommendation-9223372036854775807');await capture('detail-expanded');
    await page.getByRole('link',{name:'다음 추천 기록'}).click();await expect(page.getByRole('heading',{name:'MSFT',exact:true})).toBeVisible();await capture('detail-next');
    for(const [scenario,target,text] of [
      ['empty','/performance/evaluations','저장된 평가가 아직 없습니다.'],
      ['legacy','/performance/evaluations/9','이 과거 평가에는 상세 추천 기록이 저장되지 않았습니다.'],
      ['count-mismatch','/performance/evaluations/9','전체 기록 수가 맞지 않습니다.'],
      ['corrupt','/performance/evaluations/9','저장 내용 불일치'],
      ['unchanged','/performance/evaluations/9','비교한 추천·투자 논리 항목이 같습니다.'],
      ['source-missing','/performance/evaluations/9','현재 추천 없음'],
      ['source-unavailable','/performance/evaluations/9','현재 자료 조회 불가'],
      ['unavailable','/performance/evaluations','평가 기록을 불러오지 못했습니다'],
      ['missing','/performance/evaluations/9','요청한 평가 기록이 없습니다'],
      ['malformed','/performance/evaluations/9','평가 기록을 불러오지 못했습니다'],
      ['healthy','/performance/evaluations/01','조회 주소를 확인해 주세요']]){
      mode=scenario;await page.goto('http://127.0.0.1:13019'+target);await expect(page.locator('main')).toContainText(text);await capture(scenario==='healthy'?'invalid':scenario);
    }
    await context.close();
  }
  assert(requests.every(r=>r.method==='GET'));assert(requests.every(r=>!r.path.includes('order')));
  await writeFile(path.join(out,'result.json'),JSON.stringify({passed:true,captures,request_count:requests.length,read_only:true,production_access:false},null,2));
  console.log(`PASS: ${captures.length} actual page captures; navigation, pagination, states, accessibility, overflow and read-only requests verified.`);
} finally {await browser?.close();child.kill('SIGTERM');await new Promise(resolve=>api.close(resolve));await writeFile(path.join(out,'next.log'),log);}
