import Link from "next/link";
import type { Route } from "next";

import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import {
  formatSignedPercent,
  movementMagnitudePercent,
  movementTone,
  summarizeMovementBuckets,
} from "@/lib/presentation";
import type { MovementTone } from "@/lib/presentation";
import type { StockListData } from "@/lib/types";

import styles from "./StockMovementHeatmap.module.css";

type StockMovementRow = StockListData["stocks"][number];

type StockMovementHeatmapProps = {
  readonly stocks: readonly StockMovementRow[];
  readonly latestPriceDate: string | null;
};

const toneClassName: Record<MovementTone, string> = {
  down: styles.down,
  flat: styles.flat,
  unknown: styles.unknown,
  up: styles.up,
};

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function movementRank(stock: StockMovementRow): number {
  const changePct = stock.latest_price.change_pct;
  if (typeof changePct !== "number" || !Number.isFinite(changePct)) {
    return -1;
  }
  return Math.abs(changePct);
}

function dateLabel(latestPriceDate: string | null): string {
  return latestPriceDate ? `${latestPriceDate} 기준` : "가격 기준일 미확인";
}

export function StockMovementHeatmap({ stocks, latestPriceDate }: StockMovementHeatmapProps) {
  const summary = summarizeMovementBuckets(stocks.map((stock) => stock.latest_price.change_pct));
  const topMovers = stocks
    .slice()
    .sort((left, right) => movementRank(right) - movementRank(left) || left.symbol.localeCompare(right.symbol))
    .slice(0, 48);

  return (
    <section className={styles.panel} aria-labelledby="stock-movement-heatmap-title">
      <div className={styles.heading}>
        <div>
          <span>등락 지도 · {dateLabel(latestPriceDate)}</span>
          <h2 id="stock-movement-heatmap-title">오늘 크게 움직인 종목</h2>
        </div>
        <dl className={styles.summary} aria-label="종목 등락 요약">
          <div>
            <dt>상승</dt>
            <dd>{summary.upCount.toLocaleString("ko-KR")}개</dd>
          </div>
          <div>
            <dt>하락</dt>
            <dd>{summary.downCount.toLocaleString("ko-KR")}개</dd>
          </div>
          <div>
            <dt>보합</dt>
            <dd>{summary.flatCount.toLocaleString("ko-KR")}개</dd>
          </div>
          <div>
            <dt>미측정</dt>
            <dd>{summary.unknownCount.toLocaleString("ko-KR")}개</dd>
          </div>
        </dl>
      </div>

      <div className={styles.extremes} aria-label="가장 큰 상승과 하락">
        <div>
          <span>최대 상승</span>
          <strong>{formatSignedPercent(summary.strongestUp).label}</strong>
        </div>
        <div>
          <span>최대 하락</span>
          <strong>{formatSignedPercent(summary.strongestDown).label}</strong>
        </div>
        <p>
          추천 여부와 무관하게 가격이 크게 움직인 종목을 먼저 보여준다. 색은 방향, 막대 길이는 절대 등락폭을
          의미한다.
        </p>
      </div>

      <div className={styles.grid} aria-label="종목별 전일 대비 등락">
        {topMovers.map((stock) => {
          const tone = movementTone(stock.latest_price.change_pct);
          return (
            <Link className={`${styles.tile} ${toneClassName[tone]}`} href={stockHref(stock.symbol)} key={stock.symbol}>
              <span>{stock.symbol}</span>
              <strong>{stock.name}</strong>
              <SignedReturnBadge value={stock.latest_price.change_pct} />
              <i aria-hidden="true">
                <b style={{ inlineSize: `${movementMagnitudePercent(stock.latest_price.change_pct)}%` }} />
              </i>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
