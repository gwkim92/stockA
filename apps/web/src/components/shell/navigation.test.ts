import { describe, expect, it } from "vitest";
import { ALL_NAVIGATION, PRIMARY_NAVIGATION, PORTFOLIO_NAVIGATION, navigationContext, navigationResults, symbolDestination, routeIsActive } from "./navigation";
describe("research information architecture", () => {
  it("separates research from holdings and operations", () => {
    expect(PRIMARY_NAVIGATION.map(item => item.label)).toEqual(["리서치 홈","시장 현황","테마 사이클","뉴스 리서치","기업 탐색","투자 후보"]);
    expect(PORTFOLIO_NAVIGATION.map(item => item.href)).toContain("/performance");
    expect(new Set(ALL_NAVIGATION.map(item => item.href)).size).toBe(ALL_NAVIGATION.length);
  });
  it.each([["/stocks/AAPL","/stocks"],["/recommendations/recommendation-1","/recommendations"],["/themes/semiconductor","/cycle-map"],["/theses/thesis-1","/recommendations"],["/source-documents/source-1","/ai-evidence"],["/ai-evidence/blocked","/ai-evidence/blocked"],["/events/classification","/events/classification"]])("assigns %s to its actual parent", (path, expected) => expect(navigationContext(path).href).toBe(expected));
  it("does not match a prefix collision or mark all routes home", () => {
    expect(routeIsActive("/stocksfake","/stocks")).toBe(false);
    expect(routeIsActive("/market-map","/")).toBe(false);
  });
  it("finds menus by name and searches all tools without mutating their order", () => {
    expect(navigationResults("사이클").map(item => item.href)).toContain("/cycle-map");
    expect(navigationResults(" PERFORMANCE ").map(item => item.href)).toEqual(["/performance"]);
    expect(navigationResults("not-a-known-screen")).toHaveLength(0);
    expect(navigationResults("")).toEqual(ALL_NAVIGATION);
  });
  it.each([[" aapl ","/stocks/AAPL"],["BRK.B","/stocks/BRK.B"],["005930","/stocks/005930"]])("routes a valid symbol %s without a fake search API", (value, expected) => expect(symbolDestination(value)).toBe(expected));
  it.each(["https://external.test","../../etc","<script>","", "AAPL/other", "a very long query"]) ("rejects unsafe symbol %s", value => expect(symbolDestination(value)).toBeNull());
});
