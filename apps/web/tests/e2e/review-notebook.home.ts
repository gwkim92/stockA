import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {readFileSync} from 'node:fs';
const api='http://127.0.0.1:18770', route='/stocks/AAPL/review', key='stocka:company-review:v1:AAPL:instrument-aapl';
test.beforeEach(async({request})=>{await request.post(`${api}/__scenario`,{data:{scenario:'healthy'}});});
test('real source comparison and notebook are accessible without width overflow',async({page},info)=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(route);await expect(page.getByTestId('review-source-content')).toContainText('12%');
 await expect(page.getByRole('button',{name:'이 브라우저에 저장',exact:true})).toBeEnabled();
 expect((await page.locator('#review-claims h2').boundingBox())!.y).toBeLessThan(650);
 const geometry = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth,
  overflow: [...document.querySelectorAll('main *')].map(e => ({ tag:e.tagName, cls:e.className, right:e.getBoundingClientRect().right, left:e.getBoundingClientRect().left })).filter(e=>e.right>innerWidth+1 || e.left < -1).slice(0,12) }));
 await info.attach('layout-geometry', { body: JSON.stringify(geometry), contentType:'application/json' });
 await page.screenshot({path:info.outputPath(`notebook-${info.project.name}-layout.png`),fullPage:true,animations:'disabled'});
 expect(geometry.width, JSON.stringify(geometry)).toBeLessThanOrEqual(geometry.viewport+1);
 expect((await new AxeBuilder({page}).analyze()).violations).toEqual([]);expect(errors).toEqual([]);
 await page.screenshot({path:info.outputPath(`notebook-${info.project.name}.png`),fullPage:true,animations:'disabled'});
 await page.screenshot({path:info.outputPath(`notebook-${info.project.name}-viewport.png`),animations:'disabled'});
 await page.locator('a[href="#review-note"]').click();
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('서비스 매출 성장만으로 현금흐름 개선을 확정할 수 없다.');
 await page.getByLabel('반대 근거와 남은 의문',{exact:true}).fill('규제 비용과 고객 유지율 변화의 규모를 확인한다.');
 await page.getByLabel('다음에 확인할 사항',{exact:true}).fill('다음 실적의 현금 전환과 비용 항목을 대조한다.');
 await page.getByLabel('직접 정한 확인 날짜',{exact:true}).fill('2026-10-01');
 await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await page.screenshot({path:info.outputPath(`notebook-${info.project.name}-note.png`),animations:'disabled'});
 await page.getByTestId('review-draft').screenshot({path:info.outputPath(`notebook-${info.project.name}-note-full.png`),animations:'disabled'});
});
test('news to company to notebook to source and back is real navigation',async({page,request})=>{
 await page.goto('/events');await page.getByRole('link',{name:'기업 분석 →',exact:true}).first().click();
 await page.getByRole('link',{name:'근거 대조 · 검토 노트 →',exact:true}).click();await expect(page).toHaveURL(/stocks\/AAPL\/review$/);
 await page.getByRole('link',{name:'원천 문서 상세 →',exact:true}).click();await expect(page).toHaveURL(/source-documents\/source-document-1$/);
 await expect(page.getByTestId('source-excerpts')).toContainText('12%');await page.goBack();
 await expect(page.getByTestId('company-review-notebook')).toBeVisible();
 const calls=await(await request.get(`${api}/__requests`)).json();expect(calls.every((r:{method:string})=>r.method==='GET')).toBe(true);
});
test('edits survive source selection and explicit save reload with no server writes',async({page,request})=>{
 await page.goto(route);await page.getByLabel('내 판단과 근거',{exact:true}).fill('내 미저장 메모');
 await page.getByRole('combobox',{name:'대조할 문서'}).selectOption('source-document-2');
 await expect(page.getByTestId('review-source-content')).toContainText('regulatory costs');
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('내 미저장 메모');
 await page.getByLabel('숫자·통화·기간을 원천과 대조했다',{exact:true}).check();
 await page.getByLabel('직접 정한 확인 날짜',{exact:true}).fill('2026-10-01');
 await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await page.reload();await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('내 미저장 메모');
 await expect(page.getByLabel('숫자·통화·기간을 원천과 대조했다',{exact:true})).toBeChecked();
 await expect(page.getByLabel('직접 정한 확인 날짜',{exact:true})).toHaveValue('2026-10-01');
 const calls=await(await request.get(`${api}/__requests`)).json();expect(calls.every((r:{method:string})=>r.method==='GET')).toBe(true);
});
test('unlinked source query is rejected without fetching or substituting another document',async({page,request})=>{
 await page.goto(`${route}?source=private-document`);
 await expect(page.locator('#review-source')).toContainText('명시적으로 연결되지 않은 문서');
 const calls=await(await request.get(`${api}/__requests`)).json();expect(calls.some((r:{path:string})=>r.path.startsWith('/api/source-documents'))).toBe(false);
 await page.getByRole('combobox',{name:'대조할 문서'}).selectOption('source-document-1');await expect(page.getByTestId('review-source-content')).toContainText('12%');
});
test('repeated source parameters cannot choose a source silently',async({page,request})=>{
 await page.goto(`${route}?source=source-document-1&source=source-document-2`);
 await expect(page.locator('#review-source')).toContainText('명시적으로 연결되지 않은 문서');
 const calls=await(await request.get(`${api}/__requests`)).json();expect(calls.some((r:{path:string})=>r.path.startsWith('/api/source-documents'))).toBe(false);
});
for(const scenario of ['source-down','source-slow','wrong-source']){
 test(`${scenario} preserves company review and a usable draft`,async({page,request})=>{
  await request.post(`${api}/__scenario`,{data:{scenario}});await page.goto(route);
  await expect(page.locator('#review-source')).toContainText('선택한 원천을 불러오지 못했습니다');
  await expect(page.locator('#review-claims')).toContainText('현금흐름');
  await page.getByLabel('내 판단과 근거',{exact:true}).fill('원천 조회 후 재검토');
  await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
  await expect(page.locator('main')).not.toContainText('private-source-body');
 });
}
test('changed analysis does not reuse previous checks and stale export omits current claims',async({page,request})=>{
 await page.goto(route);await page.getByLabel('내 판단과 근거',{exact:true}).fill('이전 메모');
 await page.getByLabel('숫자·통화·기간을 원천과 대조했다',{exact:true}).check();
 await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await request.post(`${api}/__scenario`,{data:{scenario:'changed'}});await page.reload();
 await expect(page.getByTestId('review-draft')).toContainText('분석 묶음이 바뀌었습니다');
 await expect(page.getByRole('button',{name:'이 브라우저에 저장',exact:true})).toBeDisabled();
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 const file=await download;const text=readFileSync((await file.path())!,'utf8');expect(text).toContain('이전 메모');expect(text).not.toContain('변경된 분석:');
 await page.getByRole('button',{name:'메모만 가져와 새 기준으로 검토',exact:true}).click();
 await expect(page.getByLabel('숫자·통화·기간을 원천과 대조했다',{exact:true})).not.toBeChecked();
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('이전 메모');
 await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();await page.reload();
 await expect(page.getByTestId('review-draft')).not.toContainText('분석 묶음이 바뀌었습니다');
});
test('draft deletion is explicit and scoped to this company',async({page})=>{
 await page.goto(route);await page.evaluate(()=>localStorage.setItem('other-company-draft','preserve'));
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('삭제 대상');await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await page.getByRole('button',{name:'초안 삭제',exact:true}).click();await page.getByRole('button',{name:'취소',exact:true}).click();
 expect(await page.evaluate(key=>localStorage.getItem(key),key)).not.toBeNull();
 await page.getByRole('button',{name:'초안 삭제',exact:true}).click();await page.getByRole('button',{name:'삭제 확인',exact:true}).click();
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('');expect(await page.evaluate(key=>localStorage.getItem(key),key)).toBeNull();
 expect(await page.evaluate(()=>localStorage.getItem('other-company-draft'))).toBe('preserve');
});
test('corrupt stored note is not silently overwritten',async({page})=>{
 await page.addInitScript(key=>localStorage.setItem(key,'broken draft'),key);await page.goto(route);
 await expect(page.getByTestId('review-draft')).toContainText('저장된 초안을 읽을 수 없습니다');
 await expect(page.getByRole('button',{name:'이 브라우저에 저장',exact:true})).toBeDisabled();
 expect(await page.evaluate(key=>localStorage.getItem(key),key)).toBe('broken draft');
});
test('storage refusal leaves text export available without claiming a successful save',async({page})=>{
 await page.addInitScript(()=>{Storage.prototype.setItem=()=>{throw new DOMException('quota','QuotaExceededError');};});
 await page.goto(route);await page.getByLabel('내 판단과 근거',{exact:true}).fill('보존할 메모');
 await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await expect(page.getByTestId('review-draft')).toContainText('저장에 실패했습니다');
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('보존할 메모');
 const waiting=page.waitForEvent('download');await page.getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 expect(readFileSync((await(await waiting).path())!,'utf8')).toContain('보존할 메모');
});
test('another tab cannot silently replace unsaved notes',async({page,context})=>{
 await page.goto(route);await page.getByLabel('내 판단과 근거',{exact:true}).fill('첫 저장');await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 const other=await context.newPage();await other.goto(route);await expect(other.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('첫 저장');
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('현재 탭 미저장');
 await other.getByLabel('내 판단과 근거',{exact:true}).fill('다른 탭 저장');await other.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await expect(page.getByTestId('review-draft')).toContainText('다른 탭에서 초안이 변경');
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('현재 탭 미저장');
 await expect(page.getByRole('button',{name:'이 브라우저에 저장',exact:true})).toBeDisabled();await other.close();
});
test('switching company never loads a different company draft',async({page})=>{
 await page.goto(route);await page.getByLabel('내 판단과 근거',{exact:true}).fill('AAPL 전용');await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await page.goto('/stocks/MSFT/review');await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('');
});
test('source and note markup remain literal and export includes IDs not approval',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'literal'}});await page.goto(route);
 await expect(page.getByTestId('review-source-content')).toContainText('<script>window.compromised=true</script>');
 expect(await page.evaluate(()=>(window as unknown as {compromised?:boolean}).compromised)).toBeUndefined();
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('<script>unsafe</script>');
 const waiting=page.waitForEvent('download');await page.getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 const text=readFileSync((await(await waiting).path())!,'utf8');expect(text).toContain('    <script>unsafe</script>');expect(text).toContain('source-document-1');expect(text).toContain('추천·주문·검증 승인·일정 알림이 아닙니다');
});
for(const [scenario,text] of [['no-sources','반환된 연결 문서가 없습니다'],['no-research','저장된 리서치 요약이 없습니다'],['blocked','원천 제한이 있는 분석'],['fallback','규칙 기반·검증용 제공자 기록'],['future-source','문서 공개일이 기업 분석 기준일 이후']]){
 test(`${scenario} is not promoted to verified investment research`,async({page,request})=>{
  await request.post(`${api}/__scenario`,{data:{scenario}});await page.goto(route);await expect(page.locator('main')).toContainText(text);
 });
}
test('fund review uses exposure and limitations without company claim substitution',async({page})=>{
 await page.goto('/stocks/SPY/review');await expect(page.locator('#review-claims')).toContainText('노출·비용·제한');
 await expect(page.locator('#review-claims')).not.toContainText('서비스 매출 성장');
});

test('blocked storage reads retain a visible warning during further edits',async({page})=>{
 await page.addInitScript(()=>{Storage.prototype.getItem=()=>{throw new DOMException('unavailable','SecurityError');};});
 await page.goto(route);await expect(page.getByTestId('review-draft')).toContainText('브라우저 저장소를 사용할 수 없습니다');
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('저장 없이 원천을 검토 중');
 await expect(page.getByTestId('review-draft')).toContainText('브라우저 저장소를 사용할 수 없습니다');
 await expect(page.getByRole('button',{name:'이 브라우저에 저장',exact:true})).toBeDisabled();
 const waiting=page.waitForEvent('download');await page.getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 expect(readFileSync((await(await waiting).path())!,'utf8')).toContain('저장 없이 원천을 검토 중');
});
test('unsaved navigation can be cancelled without losing the review',async({page})=>{
 await page.goto(route);await page.getByLabel('내 판단과 근거',{exact:true}).fill('떠나기 전 저장할 메모');
 page.once('dialog',dialog=>dialog.dismiss());
 await page.getByRole('link',{name:'← 기업 리서치',exact:true}).click();
 await expect(page).toHaveURL(/stocks\/AAPL\/review$/);
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('떠나기 전 저장할 메모');
 await page.getByRole('button',{name:'이 브라우저에 저장',exact:true}).click();
 await page.getByRole('link',{name:'← 기업 리서치',exact:true}).click();
 await expect(page.getByTestId('company-workspace')).toBeVisible();
});
