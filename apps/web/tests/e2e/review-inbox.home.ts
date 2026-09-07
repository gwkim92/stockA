import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
import { draftKey, type Draft } from '../../src/lib/company-review-model';
const api='http://127.0.0.1:18770', route='/research-notes';
const draft=(symbol:string, nextDate:string, patch:Partial<Draft>={}):Draft=>({version:1,symbol,instrumentId:`instrument-${symbol.toLowerCase()}`,
 snapshot:'a'.repeat(64),asOf:'2026-09-05',savedAt:'2026-09-06T12:00:00Z',note:'검증용 개인 메모: 성장과 현금흐름의 관계를 확인한다.',
 opposition:'반대 가능성: 비용 증가가 성장을 상쇄할 수 있다.',nextAction:'다음 실적의 현금 전환과 비용 항목을 대조한다.',nextDate,checks:['numbers'],...patch});
const samples=()=>[draft('AAPL','2026-09-07'),draft('MSFT','2026-09-06',{nextAction:'확인이 미뤄진 질문을 다시 읽는다.'}),draft('SPY','',{nextAction:'상품 구성과 비용 자료를 다시 확인한다.'}),draft('005930','2026-09-10')];
async function seed(page:Page,notes:Draft[]=samples()) {
 await page.addInitScript(entries=>{for(const [key,value] of entries)localStorage.setItem(key,value);},notes.map(note=>[draftKey(note),JSON.stringify(note)]));
}
const filters=(page:Page)=>page.getByRole('group',{name:'직접 정한 확인 날짜로 필터',exact:true});
// Next also exposes an alert for route announcements. Assert the application's
// warning within its own boundary, not whichever global alert appears first.
const inboxAlert=(page:Page)=>page.getByTestId('review-inbox').getByRole('alert');
async function noCompanyFetch(request:APIRequestContext) {
 const calls:{path:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.filter(call=>/^\/api\/(stocks|source-documents)\//.test(call.path))).toEqual([]);
}
test.use({timezoneId:'Asia/Seoul'});
test.beforeEach(async({page,request})=>{await request.post(`${api}/__scenario`,{data:{scenario:'healthy'}});await page.clock.setFixedTime(new Date('2026-09-07T03:00:00Z'));});

test('inbox is accessible and actual saved text stays within desktop and mobile widths',async({page},info)=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await seed(page);await page.goto(route);await expect(page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true})).toBeVisible();
 const geometry=await page.evaluate(()=>({width:document.documentElement.scrollWidth,viewport:innerWidth}));
 expect(geometry.width).toBeLessThanOrEqual(geometry.viewport+1);
 await page.screenshot({path:info.outputPath(`inbox-${info.project.name}-viewport.png`),animations:'disabled'});
 await page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true}).click();
 await expect(page.getByTestId('saved-review-reader')).toContainText('성장과 현금흐름');await expect(page.locator('#saved-review-title')).toBeFocused();
 expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);expect(errors).toEqual([]);
 await page.screenshot({path:info.outputPath(`inbox-${info.project.name}-reading.png`),animations:'disabled'});
 await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
 await page.screenshot({path:info.outputPath(`inbox-${info.project.name}-full.png`),fullPage:true,animations:'disabled'});
 await info.attach('inbox-layout',{body:JSON.stringify(geometry),contentType:'application/json'});
});

test('real editor save opens in inbox and returns to the same current company review',async({page})=>{
 await page.goto('/stocks/AAPL/review');await page.getByLabel('내 판단과 근거',{exact:true}).fill('실제 저장 경로로 남긴 검토');
 await page.getByLabel('다음에 확인할 사항',{exact:true}).fill('현금 전환을 다시 확인한다.');await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await page.getByRole('link',{name:'내 검토함 →',exact:true}).click();await expect(page).toHaveURL(/\/research-notes$/);
 await page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true}).click();await expect(page.getByTestId('saved-review-reader')).toContainText('실제 저장 경로로 남긴 검토');
 await page.getByRole('link',{name:'현재 분석과 다시 검토 →',exact:true}).click();
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('실제 저장 경로로 남긴 검토');await expect(page.getByTestId('review-draft')).not.toContainText('분석 묶음이 바뀌었습니다');
});

test('date filters and literal search are private in-memory operations',async({page,request})=>{
 await seed(page);const urls:string[]=[];page.on('request',request=>urls.push(`${request.url()} ${request.postData()??''}`));
 await page.goto(route);await filters(page).getByRole('button',{name:/^오늘 확인/}).click();
 await expect(page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'MSFT 저장된 메모 열기',exact:true})).toHaveCount(0);
 await filters(page).getByRole('button',{name:/^날짜 지남/}).click();await expect(page.getByRole('button',{name:'MSFT 저장된 메모 열기',exact:true})).toBeVisible();
 await filters(page).getByRole('button',{name:/^전체/}).click();await page.getByLabel('종목·메모에서 찾기',{exact:true}).fill('private-query-not-for-server');
 await expect(page.getByTestId('review-inbox')).toContainText('조건에 맞는 메모가 없습니다');await expect(page).toHaveURL(/\/research-notes$/);
 expect(urls.join('\n')).not.toContain('private-query-not-for-server');await noCompanyFetch(request);
 await page.getByRole('button',{name:'검색·필터 초기화',exact:true}).click();await page.getByLabel('종목·메모에서 찾기',{exact:true}).fill('상품 구성');
 await expect(page.getByRole('button',{name:'SPY 저장된 메모 열기',exact:true})).toBeVisible();await page.reload();
 await expect(page.getByLabel('종목·메모에서 찾기',{exact:true})).toHaveValue('');await expect(page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true})).toBeVisible();
});

test('company API failure does not block reading or export and does not cause company prefetch',async({page,request})=>{
 await seed(page,[draft('AAPL','')]);await request.post(`${api}/__scenario`,{data:{scenario:'all-down'}});await page.goto(route);
 await page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true}).click();await expect(page.getByTestId('saved-review-reader')).toContainText('검증용 개인 메모');
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'이 메모 내보내기',exact:true}).click();
 const text=readFileSync((await(await pending).path())!,'utf8');expect(text).toContain('검증용 개인 메모');expect(text).toContain('최신 분석·원천은 포함하지');await noCompanyFetch(request);
});

test('complete empty storage differs from denied storage',async({page})=>{
 await page.goto(route);await expect(page.getByTestId('review-inbox')).toContainText('아직 저장한 검토가 없습니다');
 await page.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new DOMException('denied','SecurityError');}});});
 await page.reload();await expect(inboxAlert(page)).toHaveCount(1);await expect(inboxAlert(page)).toBeVisible();
 await expect(inboxAlert(page)).toContainText('저장소를 읽을 수 없습니다');await expect(page.getByTestId('review-inbox')).not.toContainText('아직 저장한 검토가 없습니다');
 await expect(page.getByRole('button',{name:'읽은 초안 묶음 내보내기',exact:true})).toBeDisabled();
});

test('corrupt and mismatched drafts stay preserved without generating a company link',async({page})=>{
 const badKey='stocka:company-review:v1:MSFT:instrument-msft';
 await page.addInitScript(({key,raw})=>{localStorage.setItem(key,'broken-original');localStorage.setItem('stocka:company-review:v1:AAPL:instrument-aapl',raw);},{key:badKey,raw:JSON.stringify(draft('SPY',''))});
 await page.goto(route);await expect(page.getByTestId('review-inbox')).toContainText('읽지 못한 초안 2개');await expect(page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true})).toHaveCount(0);
 await page.getByText('읽지 못한 초안 2개 · 원본은 보존됩니다',{exact:true}).click();expect(await page.evaluate(key=>localStorage.getItem(key),badKey)).toBe('broken-original');
 await expect(page.getByRole('link',{name:'현재 분석과 다시 검토 →',exact:true})).toHaveCount(0);
});

test('bulk export uses loaded valid notes not search results and preserves all original fields',async({page})=>{
 const notes=samples();await seed(page,notes);await page.goto(route);await page.getByLabel('종목·메모에서 찾기',{exact:true}).fill('AAPL');
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'읽은 초안 묶음 내보내기',exact:true}).click();
 const data=JSON.parse(readFileSync((await(await pending).path())!,'utf8'));expect(data.notes).toHaveLength(4);expect(data.notes.find((note:Draft)=>note.symbol==='AAPL')).toEqual(notes[0]);expect(data.scope).toBe('loaded-valid-notes-only');
 expect(await page.evaluate(key=>localStorage.getItem(key),draftKey(notes[0]))).toBe(JSON.stringify(notes[0]));
});

test('another tab updates saved notes and deletion is visible without a phantom current record',async({page,context})=>{
 await seed(page,[draft('AAPL','')]);await page.goto(route);await page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true}).click();
 const other=await context.newPage();await other.goto(route);const changed=draft('AAPL','',{note:'다른 탭에서 저장한 최신 메모'});
 await other.evaluate(({key,value})=>localStorage.setItem(key,value),{key:draftKey(changed),value:JSON.stringify(changed)});
 await expect(page.getByTestId('saved-review-reader')).toContainText('다른 탭에서 저장한 최신 메모');await other.evaluate(key=>localStorage.removeItem(key),draftKey(changed));
 await expect(page.getByTestId('saved-review-reader')).toContainText('선택했던 초안이 현재 읽은 목록에 없습니다');await expect(page.getByRole('link',{name:'현재 분석과 다시 검토 →',exact:true})).toHaveCount(0);await other.close();
});

test('large inventories are explicitly partial instead of being reported as a complete backup',async({page})=>{
 const notes=Array.from({length:201},(_,i)=>draft(`S${i}`,''));await seed(page,notes);await page.goto(route);
 await expect(inboxAlert(page)).toHaveCount(1);await expect(inboxAlert(page)).toBeVisible();
 await expect(inboxAlert(page)).toContainText('일부 항목만 읽었습니다');await expect(page.getByRole('button',{name:/저장된 메모 열기$/})).toHaveCount(200);
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'읽은 초안 묶음 내보내기',exact:true}).click();
 const data=JSON.parse(readFileSync((await(await pending).path())!,'utf8'));expect(data.completeRead).toBe(false);expect(data.notes).toHaveLength(200);
});

test('stored markup stays literal in the reader and its Markdown export',async({page})=>{
 await seed(page,[draft('AAPL','',{note:'<script>window.inboxCompromised=true</script>\n# private heading'})]);await page.goto(route);
 await page.getByRole('button',{name:'AAPL 저장된 메모 열기',exact:true}).click();await expect(page.getByTestId('saved-review-reader')).toContainText('<script>window.inboxCompromised=true</script>');
 expect(await page.evaluate(()=>(window as unknown as {inboxCompromised?:boolean}).inboxCompromised)).toBeUndefined();
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'이 메모 내보내기',exact:true}).click();
 expect(readFileSync((await(await pending).path())!,'utf8')).toContain('    <script>window.inboxCompromised=true</script>\n    # private heading');
});

test('returning after local midnight reclassifies chosen dates without creating reminders',async({page})=>{
 await seed(page,[draft('AAPL','2026-09-07')]);await page.goto(route);await expect(filters(page).getByRole('button',{name:/^오늘 확인/})).toContainText('1');
 await page.clock.setFixedTime(new Date('2026-09-07T15:01:00Z'));await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
 await expect(page.getByTestId('review-inbox')).toContainText('기기 날짜 2026-09-08');await expect(filters(page).getByRole('button',{name:/^날짜 지남/})).toContainText('1');
});
