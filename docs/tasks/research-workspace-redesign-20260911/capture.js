async (page) => {
  const output = 'output/playwright/research-workspace-redesign-20260911';
  const routes = [['home','/'], ['company','/stocks/NVDA'], ['financials','/stocks/NVDA?view=company-analysis'], ['fund','/stocks/SPY?view=company-analysis'], ['news','/intelligence'], ['holdings','/portfolio/coverage']];
  const results = [];
  for (const [size, width, height] of [['desktop',1440,900], ['mobile',390,844]]) {
    await page.setViewportSize({width,height});
    for (const [name,path] of routes) {
      const errors = []; const listener = e => errors.push(e.message); page.on('pageerror',listener);
      const response = await page.goto(`http://127.0.0.1:13321${path}`);
      await page.locator('main h1').first().waitFor();
      await page.screenshot({path:`${output}/${name}-${size}.png`,animations:'disabled'});
      const dimensions = await page.evaluate(() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth, height:document.documentElement.scrollHeight}));
      results.push({name,size,path,status:response.status(),...dimensions,errors});
      page.off('pageerror',listener);
    }
  }
  return results;
}
