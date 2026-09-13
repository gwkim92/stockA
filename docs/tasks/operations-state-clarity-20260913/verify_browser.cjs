const ROOT=require('path').resolve(__dirname,'../../..');
const {chromium,expect}=require(ROOT+'/apps/web/node_modules/@playwright/test');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true}); const results=[];
 try {for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
  const page=await browser.newPage({viewport:{width,height},isMobile:name==='mobile',hasTouch:name==='mobile'});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const response=await page.goto('http://127.0.0.1:13309/data-health',{waitUntil:'networkidle'});
  if(response.status()!==200) throw Error('HTTP '+response.status());
  await page.locator('#investment-quality-details > summary').click();
  const feedback=page.locator('#portfolio-review-feedback');
  const amzn=feedback.locator('tbody tr').filter({has:page.getByText('AMZN',{exact:true})});
  await expect(amzn).toHaveCount(1);
  await expect(amzn).toContainText('판단 보류');
  await expect(amzn).toContainText('수치 근거는 있지만');
  await amzn.scrollIntoViewIfNeeded();
  await amzn.screenshot({path:__dirname+'/evidence/feedback-'+name+'.png'});
  const calibration=page.locator('#portfolio-review-calibration');
  await expect(calibration).toContainText('같은 결정을 여러 날짜에 평가한 기록');
  await expect(calibration).toContainText('성숙한 누적 관찰');
  await expect(calibration).toContainText('454/10');
  await expect(calibration).toContainText('미확정 관찰 96건');
  await calibration.scrollIntoViewIfNeeded();
  await calibration.screenshot({path:__dirname+'/evidence/calibration-'+name+'.png'});
  // Open the real disclosure controls to inspect the run history.
  for(const detail of await page.locator('details').all()){
   if(await detail.getAttribute('open')===null){
    const summary=detail.locator(':scope > summary');
    if(await summary.isVisible()) await summary.click();
   }
  }
  const rows=page.locator('tr').filter({hasText:'다음 일정 대기'});
  if(await rows.count()<2) throw Error('Expected both scheduled waits in execution history');
  const texts=await rows.allTextContents();
  const metrics=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  if(metrics.scrollWidth>metrics.width) throw Error('Page overflow: '+JSON.stringify(metrics));
  if(errors.length) throw Error(errors.join('\n'));
  await rows.first().scrollIntoViewIfNeeded();
  await page.screenshot({path:__dirname+'/evidence/scheduled-wait-'+name+'.png'});
  results.push({name,http:response.status(),amzn:await amzn.innerText(),scheduledWaits:texts,metrics,errors});
  const coverage=await page.goto('http://127.0.0.1:13309/portfolio/coverage',{waitUntil:'networkidle'});
  await expect(page.locator('#portfolio-outcome-boundary')).toContainText('같은 결정을 여러 날짜에 평가한 기록');
  results[results.length-1].coverageHttp=coverage.status();
  await page.close();
 }}finally{await browser.close();}
 fs.writeFileSync(__dirname+'/evidence/browser.json',JSON.stringify(results,null,2));
 console.log(JSON.stringify(results));
})().catch(e=>{console.error(e);process.exit(1)});
