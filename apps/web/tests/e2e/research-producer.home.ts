import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFileSync } from 'node:fs';
const api='http://127.0.0.1:18770', route='/stocks/AAPL/review';
// Scope to the active workspace: client navigation can briefly retain the old
// and new page. Do not weaken assertions by selecting whichever notice is first.
const companyNotice=(page:Page)=>page.getByTestId('company-workspace').getByTestId('research-data-notice');
const notebook=(page:Page)=>page.getByTestId('company-review-notebook');
const notebookNotice=(page:Page)=>notebook(page).getByTestId('research-data-notice');

test('actual producer normal claims and exact source identifiers reach the rendered notebook',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-valid'}});
 await page.goto('/stocks/AAPL');await expect(page.locator('#company-case')).toContainText('정상 주장');
 await expect(companyNotice(page)).toHaveCount(0);
 await page.getByRole('link',{name:'근거 대조 · 검토 노트 →',exact:true}).click();
 await expect(page).toHaveURL(/\/stocks\/AAPL\/review$/);await expect(notebook(page)).toBeVisible();
 await expect(page.locator('#review-claims')).toContainText('정상 주장');
 await expect(notebookNotice(page)).toHaveCount(0);
 await expect(page.getByRole('radio',{name:/source-document-7001/})).toBeChecked();
 await expect(page.getByRole('link',{name:'원천 문서 상세 →',exact:true})).toHaveAttribute('href','/source-documents/source-document-7001');
 const calls:{path:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.some(call=>call.path==='/api/source-documents/source-document-7001')).toBe(true);
 expect(calls.some(call=>call.path.includes('source-document-True'))).toBe(false);
});

test('actual producer malformed values are visibly unavailable, not narrative or fabricated source links',async({page,request},info)=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-malformed'}});
 await page.goto(route);await expect(notebook(page)).toBeVisible();
 const notice=notebookNotice(page);
 await expect(notice).toHaveCount(1);await expect(notice).toBeVisible();
 await expect(notice).toHaveAttribute('role','status');await expect(notice).toHaveAttribute('aria-atomic','true');
 await expect(notice).toContainText('형식 오류');await expect(notice).toContainText('핵심 주장');
 await expect(page.locator('#review-claims')).not.toContainText('synthetic-object');
 await expect(page.locator('#review-claims')).not.toContainText('valid fragment');
 await expect(page.locator('#review-source').getByRole('radio')).toHaveCount(0);
 await expect(notebook(page).getByTestId('review-group-claims')).toContainText('형식 오류로 표시하지 않았습니다');
 await expect(notebook(page).getByTestId('review-source-count')).toHaveText('문서 수 미확인');
 await expect(page.locator('#review-source')).toContainText('리서치 입력 문서: 형식 오류');
 const calls:{path:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.filter(call=>call.path.startsWith('/api/source-documents/'))).toEqual([]);
 expect((await new AxeBuilder({page}).include('[data-testid="company-review-notebook"] [data-testid="research-data-notice"]').analyze()).violations).toEqual([]);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await page.screenshot({path:info.outputPath(`producer-contract-${info.project.name}.png`),fullPage:true,animations:'disabled'});
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('자료 오류를 확인하고 재검토한다.');
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 const exported=readFileSync((await(await pending).path())!,'utf8');
 expect(exported).toContain('자료 오류를 확인하고 재검토한다.');expect(exported).not.toContain('synthetic-object');
 expect(exported).toContain('## 리서치 데이터 상태');expect(exported).toContain('형식 오류: 핵심 주장 · 리서치 입력 문서');
 expect(exported).toContain('문서 수 미확인');expect(exported).not.toContain('0개 연결 문서');
 expect(exported).not.toContain('valid fragment');
});

test('missing producer field is different from an explicitly empty list on both research screens',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-partial'}});
 await page.goto('/stocks/AAPL');await expect(companyNotice(page)).toHaveCount(1);await expect(companyNotice(page)).toContainText('미제공');
 await page.goto(route);await expect(notebookNotice(page)).toHaveCount(1);await expect(notebookNotice(page)).toContainText('반대 근거·위험');
 await expect(notebook(page).getByTestId('review-group-risks')).toContainText('자료 미제공');
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-empty'}});
 await page.reload();await expect(notebook(page)).toBeVisible();await expect(notebookNotice(page)).toHaveCount(0);
 await expect(page.locator('#review-claims')).toContainText('반환된 목록이 비어 있습니다');
 await expect(notebook(page).getByTestId('review-source-count')).toHaveText('0개 연결 문서');
});

test('quality metadata does not change recommendation data or enable automatic review approval',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-malformed'}});
 await page.goto('/stocks/AAPL');await expect(page.locator('#company-case')).toContainText('형식 오류');
 await expect(page.getByRole('link',{name:'추천 판단서 열기',exact:true})).toHaveAttribute('href','/recommendations/recommendation-1');
 await page.getByRole('link',{name:'근거 대조 · 검토 노트 →',exact:true}).click();
 await expect(page).toHaveURL(/\/stocks\/AAPL\/review$/);await expect(notebook(page)).toBeVisible();
 await expect(page.getByLabel('숫자·통화·기간을 원천과 대조했다',{exact:true})).not.toBeChecked();
 await expect(notebookNotice(page)).toHaveCount(1);await expect(notebookNotice(page)).toContainText('분석의 사실성·투자 판단 검증과 별개');
});

async function exportedNote(page: Page): Promise<string> {
 const pending=page.waitForEvent('download');
 await notebook(page).getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 return readFileSync((await(await pending).path())!,'utf8');
}

test('missing source inventory remains unknown in the notebook and portable export',async({page,request},info)=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-missing-sources'}});
 await page.goto(route);await expect(notebook(page)).toBeVisible();
 await expect(notebook(page).getByTestId('review-source-count')).toHaveText('문서 수 미확인');
 await expect(page.locator('#review-source')).toContainText('리서치 입력 문서: 자료 미제공');
 await expect(page.locator('#review-source').getByRole('radio')).toHaveCount(0);
 const calls:{path:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.filter(call=>call.path.startsWith('/api/source-documents/'))).toEqual([]);
 const exported=await exportedNote(page);
 expect(exported).toContain('미제공: 리서치 입력 문서');expect(exported).toContain('문서 수 미확인');
 expect(exported).not.toContain('0개 연결 문서');expect(exported).not.toContain('형식 오류:');
 await page.locator('#review-source').screenshot({path:info.outputPath(`missing-sources-${info.project.name}.png`),animations:'disabled'});
});

test('separate event documents remain usable without replacing invalid research inputs',async({page,request},info)=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-malformed-events'}});
 await page.goto(route);await expect(notebook(page)).toBeVisible();
 await expect(notebook(page).getByTestId('review-source-count')).toHaveText('현재 표시 3개');
 await expect(notebook(page).getByTestId('review-source-scope')).toContainText('대신하지 않습니다');
 await expect(page.getByRole('radio',{name:'서비스 성장과 현금흐름 기업 직접 연결',exact:true})).toBeChecked();
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('원래 리서치 입력은 확인하지 못했다.');
 await page.getByRole('radio',{name:'별도 시장 배경 자료 시장 배경 연결',exact:true}).check();
 await expect(page).toHaveURL(/source=source-document-3/);
 await expect(page.getByRole('link',{name:'원천 문서 상세 →',exact:true})).toHaveAttribute('href','/source-documents/source-document-3');
 await expect(page.getByLabel('내 판단과 근거',{exact:true})).toHaveValue('원래 리서치 입력은 확인하지 못했다.');
 const exported=await exportedNote(page);
 expect(exported).toContain('원래 리서치 입력은 확인하지 못했다.');expect(exported).toContain('형식 오류: 핵심 주장 · 리서치 입력 문서');
 expect(exported).toContain('연결 경로: 기업 직접 연결');expect(exported).toContain('연결 경로: 시장 배경 연결');
 expect(exported).not.toContain('연결 경로: 리서치 입력 문서');expect(exported).not.toContain('source-document-7001');
 const calls:{path:string;method:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.filter(call=>call.path.startsWith('/api/source-documents/')).every(call=>['/api/source-documents/source-document-1','/api/source-documents/source-document-3'].includes(call.path))).toBe(true);
 expect(calls.every(call=>call.method==='GET')).toBe(true);
 expect((await new AxeBuilder({page}).include('[data-testid="company-review-notebook"]').analyze()).violations).toEqual([]);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await page.locator('#review-source').screenshot({path:info.outputPath(`independent-sources-${info.project.name}.png`),animations:'disabled'});
});

test('corrupt quality metadata has the same safe explanation in screen and export',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-metadata-invalid'}});
 await page.goto(route);await expect(notebook(page)).toBeVisible();
 await expect(notebookNotice(page)).toContainText('데이터 상태를 확인할 수 없습니다');
 await expect(notebook(page).getByTestId('review-group-claims')).toContainText('데이터 상태를 확인할 수 없어');
 await expect(notebook(page).getByTestId('review-source-count')).toHaveText('문서 수 미확인');
 await expect(page.locator('#review-source').getByRole('radio')).toHaveCount(0);
 const exported=await exportedNote(page);
 expect(exported).toContain('리서치 데이터 상태를 확인할 수 없습니다');
 expect(exported).not.toContain('unexpected-private-metadata');expect(exported).not.toContain('정상 주장');
 expect(exported).not.toContain('source-document-7001');
 const calls:{path:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.filter(call=>call.path.startsWith('/api/source-documents/'))).toEqual([]);
});

test('a rejected summary is explained where it would be read and exported',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-bad-summary'}});
 await page.goto(route);await expect(notebook(page)).toBeVisible();
 await expect(page.locator('#review-claims')).toContainText('요약: 형식 오류로 표시하지 않았습니다');
 await expect(page.locator('#review-claims')).toContainText('정상 주장');
 const exported=await exportedNote(page);
 expect(exported).toContain('형식 오류: 요약');expect(exported).toContain('요약: 형식 오류로 표시하지 않았습니다');
 expect(exported).toContain('정상 주장');expect(exported).not.toContain('synthetic-summary');
});
