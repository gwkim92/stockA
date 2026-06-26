"use client";

import { useMemo, useState } from "react";

import { koCode } from "@/lib/korean-labels";
import type { StockMarketDataProvider, StockPrice, StockTossProviderEvidence } from "@/lib/types";

type CandleRange = "1M" | "3M" | "6M" | "1Y";

const RANGE_LIMITS: Record<CandleRange, number> = {
  "1M": 22,
  "3M": 66,
  "6M": 132,
  "1Y": 252,
};

function formatCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatCompact(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

function usableCandle(bar: StockPrice) {
  return (
    typeof bar.open === "number"
    && typeof bar.high === "number"
    && typeof bar.low === "number"
    && typeof bar.close === "number"
    && bar.high >= bar.low
  );
}

function providerLabel(value: string | null | undefined) {
  if (!value || value.toLowerCase() === "missing") {
    return "원천 대기";
  }
  return koCode(value);
}

export function CandlestickChart({
  bars,
  currencyCode,
  provider,
  tossEvidence,
}: {
  bars: StockPrice[];
  currencyCode: string;
  provider: StockMarketDataProvider;
  tossEvidence: StockTossProviderEvidence;
}) {
  const [range, setRange] = useState<CandleRange>("3M");
  const plotted = useMemo(() => {
    const limit = RANGE_LIMITS[range];
    return bars.filter(usableCandle).slice(-limit);
  }, [bars, range]);

  if (plotted.length < 2) {
    return <div className="empty-state">차트를 그릴 만큼 가격 데이터가 아직 충분하지 않다.</div>;
  }

  const width = 860;
  const height = 320;
  const chartTop = 34;
  const chartHeight = 184;
  const volumeTop = 238;
  const volumeHeight = 52;
  const minPrice = Math.min(...plotted.map((bar) => bar.low as number));
  const maxPrice = Math.max(...plotted.map((bar) => bar.high as number));
  const priceRange = maxPrice - minPrice || 1;
  const maxVolume = Math.max(...plotted.map((bar) => bar.volume || 0), 1);
  const slot = 780 / Math.max(plotted.length, 1);
  const candleWidth = Math.max(3, Math.min(12, slot * 0.52));
  const first = plotted[0];
  const last = plotted[plotted.length - 1];
  const priceY = (value: number) => chartTop + (1 - (value - minPrice) / priceRange) * chartHeight;
  const analysisSource = provider.analysis_price_source;
  const brokerSource = provider.broker_price_source;
  const brokerStatus =
    tossEvidence.comparison.status_label
    || brokerSource.status_label
    || (tossEvidence.status === "available" ? "토스증권 가격 수집됨" : "토스증권 가격 대기");

  return (
    <figure className="candlestick-chart" aria-label="캔들 차트">
      <div className="chart-toolbar">
        <div className="chart-provider-stack">
          <span className={`provider-chip is-${provider.freshness_status}`}>
            {analysisSource.label} · {providerLabel(analysisSource.provider)}
          </span>
          <span className="provider-note">
            {brokerSource.label} · {brokerStatus} · 추천 점수 미반영
          </span>
        </div>
        <div className="range-segments" role="tablist" aria-label="캔들 기간">
          {(Object.keys(RANGE_LIMITS) as CandleRange[]).map((item) => (
            <button
              aria-selected={range === item}
              className={range === item ? "is-active" : ""}
              key={item}
              onClick={() => setRange(item)}
              role="tab"
              type="button"
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby="candlestick-chart-title">
        <title id="candlestick-chart-title">수집된 일봉 캔들 흐름</title>
        <line className="chart-grid-line" x1="40" x2="820" y1={chartTop} y2={chartTop} />
        <line className="chart-grid-line" x1="40" x2="820" y1={chartTop + chartHeight / 2} y2={chartTop + chartHeight / 2} />
        <line className="chart-grid-line" x1="40" x2="820" y1={chartTop + chartHeight} y2={chartTop + chartHeight} />
        <line className="chart-volume-baseline" x1="40" x2="820" y1={volumeTop + volumeHeight} y2={volumeTop + volumeHeight} />

        {plotted.map((bar, index) => {
          const open = bar.open as number;
          const close = bar.close as number;
          const high = bar.high as number;
          const low = bar.low as number;
          const up = close >= open;
          const x = 40 + slot / 2 + index * slot;
          const bodyTop = priceY(Math.max(open, close));
          const bodyHeight = Math.max(2, Math.abs(priceY(open) - priceY(close)));
          const volumeHeightValue = ((bar.volume || 0) / maxVolume) * volumeHeight;
          return (
            <g className={up ? "candle is-up" : "candle is-down"} key={`${bar.trade_date}-${index}`}>
              <line x1={x} x2={x} y1={priceY(high)} y2={priceY(low)} />
              <rect x={x - candleWidth / 2} y={bodyTop} width={candleWidth} height={bodyHeight} rx="1.5" />
              <rect
                className="volume-bar"
                x={x - candleWidth / 2}
                y={volumeTop + volumeHeight - volumeHeightValue}
                width={candleWidth}
                height={Math.max(1, volumeHeightValue)}
                rx="1"
              />
            </g>
          );
        })}

        <text className="chart-axis-label" x="40" y="24">{formatCurrency(maxPrice, currencyCode)}</text>
        <text className="chart-axis-label" x="820" y={chartTop + chartHeight + 18} textAnchor="end">
          {formatCurrency(minPrice, currencyCode)}
        </text>
        <text className="chart-axis-label" x="40" y="310">{first.trade_date}</text>
        <text className="chart-axis-label" x="820" y="310" textAnchor="end">{last.trade_date}</text>
      </svg>

      <figcaption>
        <span>거래일 {plotted.length.toLocaleString("ko-KR")}개</span>
        <span>최근 종가 {formatCurrency(last.close, currencyCode)}</span>
        <span>최근 거래량 {formatCompact(last.volume)}</span>
      </figcaption>
    </figure>
  );
}
