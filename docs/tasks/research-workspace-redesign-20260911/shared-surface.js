async (page) => {
  const checks = [];
  for (const [size,width,height] of [['desktop',1440,900],['mobile',390,844]]) {
    await page.setViewportSize({width,height});
    for (const [name,path] of [['stocks','/stocks'],['candidates','/recommendations'],['market','/market-map'],['cycles','/cycle-map'],['performance','/performance'],['health','/data-health'],['models','/admin/ai-agents']]) {
      const errors=[]; const listener=e=>errors.push(e.message); page.on('pageerror',listener);
      const response=await page.goto(`http://127.0.0.1:13321${path}`);
      await page.locator('main h1').first().waitFor();
      const heading=await page.locator('main h1').first().innerText();
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      await page.screenshot({path:`output/playwright/research-workspace-redesign-20260911/shared-${name}-${size}.png`,animations:'disabled'});
      checks.push({size,path,status:response.status(),heading,overflow,errors});page.off('pageerror',listener);
    }
  }
  await page.setViewportSize({width:768,height:900});
  for (const path of ['/stocks/NVDA?view=company-analysis','/intelligence','/portfolio/coverage']) {
    await page.goto(`http://127.0.0.1:13321${path}`);await page.locator('main h1').first().waitFor();
    checks.push({size:'tablet',path,overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)});
  }
  return checks;
}
