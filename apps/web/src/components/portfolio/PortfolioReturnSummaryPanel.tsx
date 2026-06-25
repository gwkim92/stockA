import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import {
  calculatePortfolioReturnSummary,
  calculatePositionReturn,
  formatSignedPercent,
  portfolioCopy,
} from "@/lib/presentation";
import type { PortfolioCoverageData } from "@/lib/types";

import styles from "./PortfolioReturnSummaryPanel.module.css";

type PortfolioPosition = PortfolioCoverageData["positions"][number];

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
          <h2>보유 포지션의 평가손익을 먼저 확인한다</h2>
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
        <div className={styles.tableWrap}>
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
      )}
    </article>
  );
}
