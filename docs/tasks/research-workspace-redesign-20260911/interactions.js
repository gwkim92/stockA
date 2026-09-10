async (page) => {
  const output = 'output/playwright/research-workspace-redesign-20260911';
  const checks = [];
  for (const [size,width,height] of [['desktop',1440,900],['mobile',390,844]]) {
    await page.setViewportSize({width,height});
    await page.goto('http://127.0.0.1:13321/intelligence');
    await page.getByRole('searchbox',{name:'뉴스 검색'}).waitFor();
    await page.screenshot({path:`${output}/news-${size}.png`,animations:'disabled'});
    await page.getByRole('searchbox',{name:'뉴스 검색'}).fill('금리');
    const choice = page.getByTestId('news-workspace').locator('button[id^="news-"]').first();
    await choice.click(); const url = page.url();
    await page.reload();
    const trigger = page.getByRole('button',{name:'원천 발췌 읽기 ↗',exact:true}).first();
    await trigger.click(); const drawer = page.getByRole('dialog');
    await drawer.getByText('API가 제공한 발췌·요약입니다.',{exact:false}).waitFor({timeout:12000});
    const documentHref = await drawer.getByRole('link').getAttribute('href');
    await page.screenshot({path:`${output}/source-${size}.png`,animations:'disabled'});
    await page.keyboard.press('Escape');
    const focused = await trigger.evaluate(element => element === document.activeElement);
    const unchanged = page.url() === url;
    if (size === 'mobile') await page.getByRole('button',{name:'← 뉴스 목록으로'}).click();
    const query = await page.getByRole('searchbox',{name:'뉴스 검색'}).inputValue();
    checks.push({size,documentHref,focused,unchanged,query,dialogClosed:!(await drawer.isVisible())});
    await page.goto('http://127.0.0.1:13321/portfolio/coverage');
    const row = page.getByRole('button',{name:'MSFT 검토 선택',exact:true}); await row.click(); await page.reload();
    const selected = await row.getAttribute('aria-pressed');
    const region = page.getByRole('region',{name:'보유 비교 표 · 가로 스크롤 가능'}); await region.focus(); await page.keyboard.press('ArrowRight');
    if (size === 'mobile') await page.waitForFunction(() => document.querySelector('[aria-label="보유 비교 표 · 가로 스크롤 가능"]').scrollLeft > 0);
    const table = await region.evaluate(element => ({width:element.clientWidth,scrollWidth:element.scrollWidth,scrollLeft:element.scrollLeft}));
    checks.push({size,holding:'MSFT',selected,table});
  }
  return checks;
}
