import { describe, expect, it } from "vitest";

import { PRIMARY_NAVIGATION, routeIsActive } from "./navigation";

describe("PRIMARY_NAVIGATION", () => {
  it("contains only the six investor destinations", () => {
    expect(PRIMARY_NAVIGATION.map((item) => item.label)).toEqual([
      "오늘",
      "시장",
      "리서치",
      "종목",
      "추천",
      "포트폴리오",
    ]);
  });
});

describe("routeIsActive", () => {
  it("matches nested detail routes", () => {
    expect(routeIsActive("/stocks/AAPL", "/stocks")).toBe(true);
    expect(routeIsActive("/recommendations/recommendation-1", "/recommendations")).toBe(true);
  });

  it("does not mark home active for every route", () => {
    expect(routeIsActive("/market-map", "/")).toBe(false);
  });
});
