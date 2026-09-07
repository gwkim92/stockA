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
 const calls:{path:string}[]=await(await request.get(`${api}/__requests`)).json();
 expect(calls.filter(call=>call.path.startsWith('/api/source-documents/'))).toEqual([]);
 expect((await new AxeBuilder({page}).include('[data-testid="company-review-notebook"] [data-testid="research-data-notice"]').analyze()).violations).toEqual([]);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await page.screenshot({path:info.outputPath(`producer-contract-${info.project.name}.png`),fullPage:true,animations:'disabled'});
 await page.getByLabel('내 판단과 근거',{exact:true}).fill('자료 오류를 확인하고 재검토한다.');
 const pending=page.waitForEvent('download');await page.getByRole('button',{name:'검토 노트 내보내기',exact:true}).click();
 const exported=readFileSync((await(await pending).path())!,'utf8');
 expect(exported).toContain('자료 오류를 확인하고 재검토한다.');expect(exported).not.toContain('synthetic-object');
});

test('missing producer field is different from an explicitly empty list on both research screens',async({page,request})=>{
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-partial'}});
 await page.goto('/stocks/AAPL');await expect(companyNotice(page)).toHaveCount(1);await expect(companyNotice(page)).toContainText('미제공');
 await page.goto(route);await expect(notebookNotice(page)).toHaveCount(1);await expect(notebookNotice(page)).toContainText('반대 근거·위험');
 await request.post(`${api}/__scenario`,{data:{scenario:'producer-empty'}});
 await page.reload();await expect(notebook(page)).toBeVisible();await expect(notebookNotice(page)).toHaveCount(0);
 await expect(page.locator('#review-claims')).toContainText('반환된 목록이 비어 있습니다');
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
