import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test.beforeEach(async ({request}) => { await request.post("http://127.0.0.1:18765/__scenario",{data:{scenario:"healthy"}}); });

test("global research shell is accessible and captures actual viewport", async ({page},info) => {
  await page.goto("/");
  await expect(page.getByRole("heading",{name:"리서치 브리핑",exact:true})).toBeVisible();
  if(info.project.name === "mobile") {
    await expect(page.getByRole("navigation",{name:"모바일 주요 메뉴"})).toBeVisible();
    await expect(page.getByRole("complementary",{name:"리서치 사이드바"})).not.toBeVisible();
  } else {
    const sidebar=page.getByRole("complementary",{name:"리서치 사이드바"});
    await expect(sidebar).toBeVisible();
    await expect(sidebar.locator('[aria-current="page"]')).toHaveCount(1);
    const heading=await page.getByRole("heading",{name:"검토할 투자 후보",exact:true}).boundingBox();
    expect(heading!.y).toBeLessThan(1000);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
  const axe = await new AxeBuilder({page}).analyze();expect(axe.violations).toEqual([]);
  await page.screenshot({path:info.outputPath(`workspace-home-${info.project.name}.png`),fullPage:true,animations:"disabled"});
  await page.screenshot({path:info.outputPath(`workspace-home-${info.project.name}-viewport.png`),animations:"disabled"});
});

test("quick navigation searches, rejects unsafe symbols and closes with focus return",async({page})=>{
  await page.goto("/");
  const trigger=page.getByRole("button",{name:"화면 및 종목 코드 찾기"});await trigger.click();
  const dialog=page.getByRole("dialog");await expect(dialog).toBeVisible();
  const input=dialog.getByRole("textbox");await expect(input).toBeFocused();
  await input.fill("aapl");await expect(dialog.getByRole("link",{name:/AAPL 종목 리서치/})).toHaveAttribute("href","/stocks/AAPL");
  await input.fill("https://bad.test");await expect(dialog.getByRole("link")).toHaveCount(0);
  await input.fill("성과");await expect(dialog.getByRole("link",{name:/판단 성과/})).toHaveAttribute("href","/performance");
  const axe = await new AxeBuilder({page}).include("dialog").analyze();expect(axe.violations).toEqual([]);
  await page.keyboard.press("Escape");await expect(dialog).not.toBeVisible();await expect(trigger).toBeFocused();
  await page.keyboard.press("Control+k");await expect(dialog).toBeVisible();await page.keyboard.press("Escape");
});

test("candidate search and filters work on the production route",async({page},info)=>{
  await page.goto("/recommendations");
  const explorer=page.getByTestId("recommendation-explorer");await expect(explorer).toBeVisible();
  await expect(explorer.getByRole("link",{name:"AAPL",exact:true})).toBeVisible();
  await page.screenshot({path:info.outputPath(`workspace-candidates-${info.project.name}.png`),fullPage:true,animations:"disabled"});
  await explorer.getByRole("button",{name:/원천 제한/}).click();
  await expect(explorer.getByRole("link",{name:"AAPL",exact:true})).toHaveCount(0);
  await expect(explorer.getByRole("link",{name:"EROK",exact:true})).toBeVisible();
  await explorer.getByRole("textbox").fill("missing-company");await expect(explorer.getByRole("heading",{name:"조건에 맞는 후보가 없습니다"})).toBeVisible();
  await explorer.getByRole("button",{name:"필터 초기화"}).click();
  await expect(explorer.getByRole("link",{name:"AAPL",exact:true})).toBeVisible();
  await explorer.getByRole("link",{name:"AAPL 투자 판단서 열기"}).click();await expect(page).toHaveURL(/recommendations\/recommendation-1$/);
  await expect(page.getByTestId("investment-memo")).toBeVisible();
});

test("memo chapter links resolve and shared redesign does not obscure the evidence",async({page},info)=>{
  await page.goto("/recommendations/recommendation-1");
  const nav=page.getByRole("navigation",{name:"투자 판단서 목차"});await expect(nav).toBeVisible();
  for(const link of await nav.getByRole("link").all()) {
    const href=await link.getAttribute("href");expect(href).toMatch(/^#memo-/);await expect(page.locator(href!)).toHaveCount(1);
  }
  // Capture the initial reading state before anchor navigation changes focus/scroll.
  await page.waitForFunction(() => window.scrollY === 0);
  const titleSize = await page.locator("#recommendation-detail-title").evaluate(el => parseFloat(getComputedStyle(el).fontSize));
  expect(titleSize).toBeLessThanOrEqual(34);
  await page.screenshot({path:info.outputPath(`workspace-memo-${info.project.name}.png`),fullPage:true,animations:"disabled"});
  await page.screenshot({path:info.outputPath(`workspace-memo-${info.project.name}-viewport.png`),animations:"disabled"});
  await nav.getByRole("link",{name:"무효화",exact:true}).click();
  await expect(page.locator("#memo-conditions")).toBeInViewport();
});

test("all menus remain discoverable and selection closes the modal",async({page})=>{
  await page.goto("/");await page.getByRole("button",{name:"화면 및 종목 코드 찾기"}).click();
  const dialog=page.getByRole("dialog");await dialog.getByRole("textbox").fill("없는화면");
  await expect(dialog).toContainText("일치하는 화면이 없습니다");
  await dialog.getByRole("textbox").fill("투자 후보");await dialog.getByRole("link",{name:/투자 후보/}).click();
  await expect(page).toHaveURL(/\/recommendations$/);await expect(dialog).not.toBeVisible();
});

test("global failure preserves navigation without leaking backend error text",async({page,request})=>{
  await request.post("http://127.0.0.1:18765/__scenario",{data:{scenario:"all-down"}});
  await page.goto("/recommendations");
  await expect(page.getByRole("heading",{name:"이 화면의 자료를 불러오지 못했습니다"})).toBeVisible();
  await expect(page.locator("body")).not.toContainText("test-internal-token-must-not-render");
  await expect(page.getByRole("button",{name:"다시 시도"})).toBeVisible();
  await expect(page.getByRole("link",{name:"리서치 홈으로",exact:true})).toBeVisible();
});

test("reduced motion and intermediate viewport keep research reachable",async({page},info)=>{
  await page.emulateMedia({reducedMotion:"reduce"});
  await page.setViewportSize({width: info.project.name === "mobile" ? 360 : 1024,height:900});
  await page.goto("/");await expect(page.getByRole("heading",{name:"검토할 투자 후보",exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth+1)).toBe(true);
});
