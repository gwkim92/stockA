async (page) => {
 const base=page.url().split('/').slice(0,3).join('/'), result=[];
 const home=async()=>{await page.goto(base+'/performance/recommendations');await page.getByRole('heading',{name:'추천별 측정 결과'}).waitFor();};
 await home();
 for(const name of ['추천 기록 →','연결 투자 논리 →','평가 보존본 · 2026-09-10 →']) {
  const link=page.locator('article[aria-label$=성과]').first().getByRole('link',{name,exact:true});
  const href=await link.getAttribute('href');
  await link.click();await page.waitForURL(base+href);await page.locator('main h1').first().waitFor();
  const text=await page.locator('main').innerText();
  if(/불러오지 못했|요청한 .* 없습니다/.test(text)) throw Error('Detail read failed: '+href);
  result.push({link:name,url:page.url(),heading:await page.locator('main h1').first().innerText(),sample:text.slice(0,500)});
  if(name.startsWith('평가 보존본')) {
   const first=page.locator('main article').first();await first.waitFor();
   const evidence=await first.innerText();if(!evidence.includes('SPY'))throw Error('Wrong snapshot target');
   result[result.length-1].snapshot=evidence.slice(0,700);
   await page.screenshot({path:'output/playwright/outcome-explorer-local-snapshot.png',animations:'disabled'});
  }
  await home();
 }
 for(const [query,heading] of [['?symbol=NOSUCHSYMBOL','조건에 맞는 저장 성과가 없습니다'],['?from_date=2026-09-10&to_date=2026-01-01','조회 조건을 확인해 주세요']]) {
  await page.goto(base+'/performance/recommendations'+query);
  await page.getByRole('heading',{name:heading,exact:true}).waitFor();
  result.push({url:page.url(),heading});
 }
 await home();return result;
}
