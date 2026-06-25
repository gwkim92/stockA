import type { Route } from "next";
import Link from "next/link";

import { DecisionSummary } from "@/components/research/DecisionSummary";
import { MetricStrip } from "@/components/research/MetricStrip";
import { ResearchSection } from "@/components/research/ResearchSection";
import { StatusBadge } from "@/components/status/StatusBadge";
import { getStocks } from "@/lib/frontend-api";
import { formatPercent } from "@/lib/presentation";

import styles from "./StocksPage.module.css";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목" };

type StockRow = Awaited<ReturnType<typeof getStocks>>["data"]["stocks"][number];

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${encodeURIComponent(recommendationId)}` as Route;
}

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

function priorityScore(stock: StockRow) {
  return Number(Boolean(stock.recommendation)) * 2 + Number(Boolean(stock.position));
}

function stockStatus(stock: StockRow, latestPriceDate: string | null) {
  if (!stock.latest_price.trade_date || stock.latest_price.trade_date !== latestPriceDate) {
    return { kind: "stale" as const, label: "가격 확인 필요" };
  }
  if (stock.recommendation && stock.position) {
    return { kind: "watch" as const, label: "추천·보유 교차검토" };
  }
  if (stock.recommendation) {
    return { kind: "ready" as const, label: "추천 근거 있음" };
  }
  if (stock.position) {
    return { kind: "watch" as const, label: "보유 검토" };
  }
  return { kind: "empty" as const, label: "관찰 종목" };
}

function priorityReason(stock: StockRow) {
  if (stock.recommendation && stock.position) {
    return "추천 방향과 현재 보유 비중이 함께 연결되어 있다.";
  }
  if (stock.recommendation) {
    return "추천 신호가 있어 재무·밸류에이션·뉴스 근거를 확인해야 한다.";
  }
  if (stock.position) {
    return "현재 보유 중이므로 투자 논리와 위험 변화를 점검해야 한다.";
  }
  return "가격 흐름을 추적 중인 관찰 종목이다.";
}

export default async function StocksPage() {
  const { data } = await getStocks();
  const recommendedStocks = data.stocks.filter((stock) => stock.recommendation);
  const heldStocks = data.stocks.filter((stock) => stock.position);
  const staleStocks = data.stocks.filter(
    (stock) => !stock.latest_price.trade_date || stock.latest_price.trade_date !== data.summary.latest_price_date,
  );
  const priorityStocks = data.stocks
    .slice()
    .sort((left, right) => priorityScore(right) - priorityScore(left) || left.symbol.localeCompare(right.symbol))
    .slice(0, 4);
  const leadStock = priorityStocks[0] ?? null;

  return (
    <div className={styles.page}>
      <DecisionSummary
        eyebrow={`종목 리서치 · 가격 기준일 ${data.summary.latest_price_date || "미확인"}`}
        title={leadStock ? `${leadStock.symbol}, 오늘 가장 먼저 확인할 종목` : "분석할 종목을 기다리고 있습니다"}
        description="추천과 보유가 겹치는 종목을 먼저 보고, 가격 흐름과 투자 근거가 일치하는지 확인합니다."
        primaryAction={{
          href: leadStock ? stockHref(leadStock.symbol) : ("/data-health" as Route),
          label: leadStock ? `${leadStock.symbol} 분석 열기` : "데이터 상태 확인",
        }}
        secondaryActions={[
          { href: "/recommendations" as Route, label: "추천 보기" },
          { href: "/portfolio/coverage" as Route, label: "포트폴리오 보기" },
        ]}
        side={
          <div className={styles.leadSnapshot}>
            <span>우선 검토</span>
            <strong>{leadStock?.symbol ?? "대기"}</strong>
            <small>{leadStock ? priorityReason(leadStock) : "가격과 추천 데이터가 준비되면 표시됩니다."}</small>
          </div>
        }
      />

      <MetricStrip
        label="종목 리서치 현황"
        items={[
          { label: "추적 종목", value: `${data.stock_count}개`, context: "가격 데이터가 있는 전체 종목" },
          { label: "추천 연결", value: `${recommendedStocks.length}개`, context: "추천 상세와 연결된 종목" },
          { label: "보유 종목", value: `${heldStocks.length}개`, context: "포트폴리오에 포함된 종목" },
          {
            label: "가격 확인",
            value: `${staleStocks.length}개`,
            context: staleStocks.length > 0 ? "최신 기준일과 다른 종목" : "모든 가격일 일치",
          },
        ]}
      />

      <ResearchSection
        eyebrow="우선 검토"
        title="추천과 보유가 걸린 종목"
        description="투자 판단이 이미 연결된 종목만 앞에 배치했습니다."
      >
        <div className={styles.priorityGrid}>
          {priorityStocks.map((stock) => {
            const status = stockStatus(stock, data.summary.latest_price_date);
            return (
              <article className={styles.priorityCard} key={stock.symbol}>
                <div className={styles.cardHeader}>
                  <div>
                    <span>{stock.name}</span>
                    <strong>{stock.symbol}</strong>
                  </div>
                  <StatusBadge kind={status.kind} label={status.label} />
                </div>
                <p>{priorityReason(stock)}</p>
                <dl>
                  <div>
                    <dt>현재가</dt>
                    <dd>{formatCurrency(stock.latest_price.close, stock.currency_code)}</dd>
                  </div>
                  <div>
                    <dt>추천 점수</dt>
                    <dd>{stock.recommendation ? formatPercent(stock.recommendation.score) : "없음"}</dd>
                  </div>
                  <div>
                    <dt>보유 비중</dt>
                    <dd>{stock.position ? formatPercent(stock.position.weight) : "미보유"}</dd>
                  </div>
                </dl>
                <div className={styles.actions}>
                  <Link href={stockHref(stock.symbol)}>종목 분석</Link>
                  {stock.recommendation ? (
                    <Link href={recommendationHref(stock.recommendation.recommendation_id)}>추천 근거</Link>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      </ResearchSection>

      <ResearchSection eyebrow="전체 종목" title="추적 종목 현황" id="stock-list">
        <div className={styles.tableFrame}>
          <table>
            <thead>
              <tr>
                <th scope="col">종목</th>
                <th scope="col">현재가</th>
                <th scope="col">변동률</th>
                <th scope="col">추천</th>
                <th scope="col">보유 비중</th>
                <th scope="col">데이터</th>
                <th scope="col" aria-label="상세" />
              </tr>
            </thead>
            <tbody>
              {data.stocks.map((stock) => {
                const status = stockStatus(stock, data.summary.latest_price_date);
                return (
                  <tr key={stock.symbol}>
                    <th scope="row">
                      <Link className={styles.symbolLink} href={stockHref(stock.symbol)}>
                        <strong>{stock.symbol}</strong>
                        <small>{stock.name}</small>
                      </Link>
                    </th>
                    <td>{formatCurrency(stock.latest_price.close, stock.currency_code)}</td>
                    <td>{formatPercent(stock.latest_price.change_pct)}</td>
                    <td>
                      {stock.recommendation ? (
                        <Link href={recommendationHref(stock.recommendation.recommendation_id)}>
                          {formatPercent(stock.recommendation.score)}
                        </Link>
                      ) : (
                        "없음"
                      )}
                    </td>
                    <td>{stock.position ? formatPercent(stock.position.weight) : "미보유"}</td>
                    <td>
                      <StatusBadge kind={status.kind} label={status.label} />
                    </td>
                    <td>
                      <Link className={styles.rowAction} href={stockHref(stock.symbol)}>
                        열기
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </ResearchSection>
    </div>
  );
}
