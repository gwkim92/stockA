import { describe, expect, it } from "vitest";

import {
  calculatePortfolioReturnSummary,
  calculatePositionReturn,
  formatSignedPercent,
  movementMagnitudePercent,
  movementTone,
  summarizeMovementBuckets,
} from "./returns";

describe("formatSignedPercent", () => {
  it("shows explicit Korean direction and signed percent", () => {
    expect(formatSignedPercent(0.01234)).toEqual({
      label: "+1.2%",
      tone: "up",
      a11yLabel: "전일 대비 1.2% 상승",
    });
    expect(formatSignedPercent(-0.009)).toEqual({
      label: "-0.9%",
      tone: "down",
      a11yLabel: "전일 대비 0.9% 하락",
    });
  });

  it("keeps flat and missing values distinct", () => {
    expect(formatSignedPercent(0)).toEqual({
      label: "0.0%",
      tone: "flat",
      a11yLabel: "전일 대비 보합",
    });
    expect(formatSignedPercent(null)).toEqual({
      label: "미측정",
      tone: "unknown",
      a11yLabel: "전일 대비 미측정",
    });
  });
});

describe("movementTone", () => {
  it("classifies movement direction without treating missing data as flat", () => {
    expect(movementTone(0.0006)).toBe("up");
    expect(movementTone(-0.0006)).toBe("down");
    expect(movementTone(0.00001)).toBe("flat");
    expect(movementTone(undefined)).toBe("unknown");
  });
});

describe("movement visualization helpers", () => {
  it("summarizes measured, flat, missing, and strongest movements", () => {
    expect(summarizeMovementBuckets([0.035, -0.012, 0, null, 0.009])).toEqual({
      totalCount: 5,
      measuredCount: 4,
      upCount: 2,
      downCount: 1,
      flatCount: 1,
      unknownCount: 1,
      strongestUp: 0.035,
      strongestDown: -0.012,
    });
  });

  it("scales non-flat moves for visual bars without inventing values for missing data", () => {
    expect(movementMagnitudePercent(0.04, 0.08)).toBe(50);
    expect(movementMagnitudePercent(-0.001, 0.08)).toBe(8);
    expect(movementMagnitudePercent(0, 0.08)).toBe(0);
    expect(movementMagnitudePercent(null, 0.08)).toBe(0);
  });
});

describe("calculatePositionReturn", () => {
  it("uses stored unrealized PnL before deriving from market and cost", () => {
    expect(
      calculatePositionReturn({
        market_value: 1200,
        cost_basis: 1000,
        unrealized_pnl: 150,
      }),
    ).toEqual({
      unrealizedPnl: 150,
      returnPct: 0.15,
    });
  });

  it("derives unrealized PnL when only market value and cost basis exist", () => {
    expect(
      calculatePositionReturn({
        market_value: 900,
        cost_basis: 1000,
        unrealized_pnl: null,
      }),
    ).toEqual({
      unrealizedPnl: -100,
      returnPct: -0.1,
    });
  });
});

describe("calculatePortfolioReturnSummary", () => {
  it("aggregates invested capital, market value, PnL, and return", () => {
    expect(
      calculatePortfolioReturnSummary([
        { market_value: 1200, cost_basis: 1000, unrealized_pnl: 200 },
        { market_value: 450, cost_basis: 500, unrealized_pnl: null },
        { market_value: null, cost_basis: null, unrealized_pnl: null },
      ]),
    ).toEqual({
      measuredPositionCount: 2,
      marketValue: 1650,
      costBasis: 1500,
      unrealizedPnl: 150,
      returnPct: 0.1,
    });
  });
});
