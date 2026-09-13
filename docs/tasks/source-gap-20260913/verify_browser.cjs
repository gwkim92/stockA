const ROOT=require('path').resolve(__dirname,'../../..');
const {chromium,expect}=require(ROOT+'/apps/web/node_modules/@playwright/test');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true}); const results=[];
 try {for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
  const page=await browser.newPage({viewport:{width,height},isMobile:name==='mobile',hasTouch:name==='mobile'});
  const response=await page.goto('http://127.0.0.1:13309/data-health#research-refresh',{waitUntil:'networkidle'});
  if(response.status()!==200) throw Error('HTTP '+response.status());
  const section=page.locator('#research-refresh');
  await expect(section.getByRole('heading',{name:'보고서 갱신 현황'})).toBeVisible();
  const waiting=section.locator('dl > div').filter({has:page.getByText('원천 자료 대기',{exact:true})});
  await expect(waiting.locator('dd')).toHaveText(/^0\s*개$/);
  await section.locator('summary').click();
  for(const symbol of ['AAPL','ARM','NVDA']){
   await section.getByLabel('기업 찾기').fill(symbol);
   await expect(section.locator('li')).toHaveCount(1);
   await expect(section.locator('li')).toContainText('생성 대기');
   await expect(section.locator('li')).not.toContainText('재무 수집 기록 없음');
  }
  await section.getByLabel('기업 찾기').fill('AAPL');
  const metrics=await section.evaluate(el=>({width:el.clientWidth,scrollWidth:el.scrollWidth}));
  if(metrics.scrollWidth>metrics.width) throw Error('overflow');
  const content=await section.innerText();
  await page.setViewportSize({width,height:1600});
  await section.getByRole('heading',{name:'보고서 갱신 현황'}).click();
  await section.screenshot({path:__dirname+'/evidence/production-'+name+'.png'});
  results.push({name,http:response.status(),sourceWait:0,targetFiltersPassed:true,metrics,content});await page.close();
 }}finally{await browser.close();}
 fs.writeFileSync(__dirname+'/evidence/browser.json',JSON.stringify(results,null,2));
 console.log(JSON.stringify(results.map(({content,...r})=>r)));
})().catch(e=>{console.error(e);process.exit(1)});
