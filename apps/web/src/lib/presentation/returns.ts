export type MovementTone = "up" | "down" | "flat" | "unknown";

export type SignedPercentLabel = {
  readonly label: string;
  readonly tone: MovementTone;
  readonly a11yLabel: string;
};

export type SignedPercentOptions = {
  readonly metricLabel?: string;
  readonly missingLabel?: string;
  readonly upLabel?: string;
  readonly downLabel?: string;
  readonly flatLabel?: string;
};

export type PositionReturnInput = {
  readonly market_value: number | null;
  readonly cost_basis: number | null;
  readonly unrealized_pnl: number | null;
};

export type PositionReturn = {
  readonly unrealizedPnl: number | null;
  readonly returnPct: number | null;
};

export type PortfolioReturnSummary = {
  readonly measuredPositionCount: number;
  readonly marketValue: number | null;
  readonly costBasis: number | null;
  readonly unrealizedPnl: number | null;
  readonly returnPct: number | null;
};

const MOVEMENT_EPSILON = 0.00005;

function finiteOrNull(value: number | null | undefined): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatAbsPercent(value: number): string {
  return `${Math.abs(value * 100).toLocaleString("ko-KR", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  })}%`;
}

export function movementTone(value: number | null | undefined): MovementTone {
  const parsed = finiteOrNull(value);
  if (parsed === null) {
    return "unknown";
  }
  if (parsed > MOVEMENT_EPSILON) {
    return "up";
  }
  if (parsed < -MOVEMENT_EPSILON) {
    return "down";
  }
  return "flat";
}

export function formatSignedPercent(
  value: number | null | undefined,
  options: SignedPercentOptions = {},
): SignedPercentLabel {
  const tone = movementTone(value);
  const parsed = finiteOrNull(value);
  const metricLabel = options.metricLabel ?? "전일 대비";
  if (tone === "unknown" || parsed === null) {
    return {
      label: options.missingLabel ?? "미측정",
      tone,
      a11yLabel: `${metricLabel} 미측정`,
    };
  }
  if (tone === "flat") {
    return {
      label: "0.0%",
      tone,
      a11yLabel: `${metricLabel} ${options.flatLabel ?? "보합"}`,
    };
  }
  const prefix = tone === "up" ? "+" : "-";
  const direction = tone === "up" ? options.upLabel ?? "상승" : options.downLabel ?? "하락";
  return {
    label: `${prefix}${formatAbsPercent(parsed)}`,
    tone,
    a11yLabel: `${metricLabel} ${formatAbsPercent(parsed)} ${direction}`,
  };
}

export function calculatePositionReturn(position: PositionReturnInput): PositionReturn {
  const marketValue = finiteOrNull(position.market_value);
  const costBasis = finiteOrNull(position.cost_basis);
  const storedPnl = finiteOrNull(position.unrealized_pnl);
  const derivedPnl = marketValue !== null && costBasis !== null ? marketValue - costBasis : null;
  const unrealizedPnl = storedPnl ?? derivedPnl;
  const returnPct = unrealizedPnl !== null && costBasis !== null && costBasis !== 0 ? unrealizedPnl / costBasis : null;

  return { unrealizedPnl, returnPct };
}

export function calculatePortfolioReturnSummary(
  positions: readonly PositionReturnInput[],
): PortfolioReturnSummary {
  let measuredPositionCount = 0;
  let marketValue = 0;
  let costBasis = 0;
  let unrealizedPnl = 0;

  for (const position of positions) {
    const positionReturn = calculatePositionReturn(position);
    const positionMarketValue = finiteOrNull(position.market_value);
    const positionCostBasis = finiteOrNull(position.cost_basis);
    if (positionMarketValue === null || positionCostBasis === null || positionReturn.unrealizedPnl === null) {
      continue;
    }
    measuredPositionCount += 1;
    marketValue += positionMarketValue;
    costBasis += positionCostBasis;
    unrealizedPnl += positionReturn.unrealizedPnl;
  }

  if (measuredPositionCount === 0 || costBasis === 0) {
    return {
      measuredPositionCount,
      marketValue: null,
      costBasis: null,
      unrealizedPnl: null,
      returnPct: null,
    };
  }

  return {
    measuredPositionCount,
    marketValue,
    costBasis,
    unrealizedPnl,
    returnPct: unrealizedPnl / costBasis,
  };
}
