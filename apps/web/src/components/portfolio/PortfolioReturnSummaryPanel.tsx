import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import {
  calculatePortfolioReturnSummary,
  calculatePositionReturn,
  formatSignedPercent,
  movementMagnitudePercent,
  movementTone,
  portfolioCopy,
} from "@/lib/presentation";
import type { MovementTone } from "@/lib/presentation";
import type { PortfolioCoverageData } from "@/lib/types";

import styles from "./PortfolioReturnSummaryPanel.module.css";

type PortfolioPosition = PortfolioCoverageData["positions"][number];

const toneClassName: Record<MovementTone, string> = {
  down: styles.loss,
  flat: styles.flat,
  unknown: styles.unknown,
  up: styles.gain,
};

export type PortfolioReturnSummaryPanelProps = {
  readonly positions: readonly PortfolioPosition[];
  readonly baseCurrency: string;
};

function formatCurrency(value: number | null, currencyCode: string): string {
  if (value === null || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${(value * 100).toLocaleString("ko-KR", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  })}%`;
}

function thesisLabel(position: PortfolioPosition): string {
  return position.active_thesis_id ? "연결" : "누락";
}

function outcomeLabel(position: PortfolioPosition): string {
  if (position.coverage_status === "missing_outcome") {
    return "측정 대기";
  }
  if (position.outcome_status === "covered") {
    return "측정됨";
  }
  return portfolioCopy(position.outcome_status || null);
}

export function PortfolioReturnSummaryPanel({ positions, baseCurrency }: PortfolioReturnSummaryPanelProps) {
  const summary = calculatePortfolioReturnSummary(positions);
  const distributionRows = positions
    .map((position) => ({
      position,
      positionReturn: calculatePositionReturn(position),
    }))
    .filter((row) => row.positionReturn.returnPct !== null)
    .sort(
      (left, right) =>
        Math.abs(right.positionReturn.returnPct ?? 0) - Math.abs(left.positionReturn.returnPct ?? 0) ||
        left.position.symbol.localeCompare(right.position.symbol),
    )
    .slice(0, 10);
  const summaryReturn = formatSignedPercent(summary.returnPct, {
    metricLabel: "평가손익률",
    upLabel: "수익",
    downLabel: "손실",
    flatLabel: "보합",
  });

  return (
    <article className={`bento-card span-4 ${styles.panel}`} id="portfolio-return-summary">
      <div className="section-heading">
        <div>
          <span className="metric-sub">포트폴리오 수익률</span>
          <h2>보유 포지션의 평가손익이 먼저 보인다</h2>
        </div>
        <SignedReturnBadge
          value={summary.returnPct}
          label="평가손익률"
          options={{ metricLabel: "평가손익률", upLabel: "수익", downLabel: "손실" }}
        />
      </div>
      <p className={styles.lede}>
        손익률은 저장된 평가액, 원가, 평가손익으로 계산한 읽기 전용 현황이다. 추천 산식이나 주문 가능 여부를
        바꾸지 않는다.
      </p>
      <div className={styles.metrics} aria-label="포트폴리오 평가손익 요약">
        <div>
          <span>총 평가액</span>
          <strong>{formatCurrency(summary.marketValue, baseCurrency)}</strong>
        </div>
        <div>
          <span>투입 원가</span>
          <strong>{formatCurrency(summary.costBasis, baseCurrency)}</strong>
        </div>
        <div>
          <span>평가손익</span>
          <strong>{formatCurrency(summary.unrealizedPnl, baseCurrency)}</strong>
        </div>
        <div>
          <span>수익률</span>
          <strong>{summaryReturn.label}</strong>
        </div>
        <div>
          <span>측정 포지션</span>
          <strong>{summary.measuredPositionCount.toLocaleString("ko-KR")}개</strong>
        </div>
      </div>
      {positions.length === 0 ? (
        <p className="empty-state">
          이 기준일에는 보유 스냅샷이 없어 평가손익률을 계산할 수 없다.
        </p>
      ) : (
        <>
          <section className={styles.distribution} aria-labelledby="portfolio-return-distribution-title">
            <div>
              <span>수익률 분포</span>
              <h3 id="portfolio-return-distribution-title">성과를 끌어올린 포지션과 누른 포지션</h3>
            </div>
            <div className={styles.distributionRows}>
              {distributionRows.length > 0 ? (
                distributionRows.map((row) => {
                  const tone = movementTone(row.positionReturn.returnPct);
                  return (
                    <div className={styles.distributionRow} key={row.position.instrument_id}>
                      <strong>{row.position.symbol}</strong>
                      <div className={styles.barTrack} aria-hidden="true">
                        <b
                          className={toneClassName[tone]}
                          style={{ inlineSize: `${movementMagnitudePercent(row.positionReturn.returnPct, 0.5)}%` }}
                        />
                      </div>
                      <SignedReturnBadge
                        value={row.positionReturn.returnPct}
                        label="평가손익률"
                        options={{ metricLabel: `${row.position.symbol} 평가손익률`, upLabel: "수익", downLabel: "손실" }}
                      />
                      <small>{formatCurrency(row.positionReturn.unrealizedPnl, baseCurrency)}</small>
                    </div>
                  );
                })
              ) : (
                <p className="empty-state">원가와 평가액이 함께 있는 포지션이 없어 수익률 분포를 계산할 수 없다.</p>
              )}
            </div>
          </section>
          <div className={styles.tableWrap} tabIndex={0} aria-label="보유 포지션 평가손익 표">
            <table className={styles.table}>
              <thead>
                <tr>
                  <th scope="col">종목</th>
                  <th scope="col">평가액</th>
                  <th scope="col">평가손익</th>
                  <th scope="col">수익률</th>
                  <th scope="col">비중</th>
                  <th scope="col">투자 논리</th>
                  <th scope="col">성과</th>
                  <th scope="col">필요 조치</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position) => {
                  const positionReturn = calculatePositionReturn(position);
                  return (
                    <tr key={position.instrument_id}>
                      <th scope="row">{position.symbol}</th>
                      <td>{formatCurrency(position.market_value, baseCurrency)}</td>
                      <td>{formatCurrency(positionReturn.unrealizedPnl, baseCurrency)}</td>
                      <td>
                        <SignedReturnBadge
                          value={positionReturn.returnPct}
                          label="평가손익률"
                          options={{ metricLabel: `${position.symbol} 평가손익률`, upLabel: "수익", downLabel: "손실" }}
                        />
                      </td>
                      <td>{formatPercent(position.weight)}</td>
                      <td>{thesisLabel(position)}</td>
                      <td>{outcomeLabel(position)}</td>
                      <td>{portfolioCopy(position.action || "유지 관찰")}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </article>
  );
}
