import Link from "next/link";
import type { Route } from "next";

import { getStocks } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목" };

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

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

export default async function StocksPage() {
  const response = await getStocks();
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="stocks-title">
        <div className="bento-badge">종목 확인실 • 수집 가격 데이터</div>
        <h1 id="stocks-title">어떤 종목 데이터가 들어와 있는지 확인한다.</h1>
        <p>
          이 화면은 추천 화면이 아니라 데이터 확인 화면이다. 현재 DB에 적재된 종목, 최신 가격일, 가격 수집 범위,
          추천 상태, 보유 여부를 한 번에 보여준다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="종목 데이터 요약">
        <div className="rail-cell">
          <span>수집 종목</span>
          <strong>{data.stock_count.toLocaleString("ko-KR")}</strong>
          <small>가격 데이터가 있는 종목</small>
        </div>
        <div className="rail-cell">
          <span>최신 가격일</span>
          <strong>{data.summary.latest_price_date || "없음"}</strong>
          <small>시장 데이터 최종 관측일</small>
        </div>
        <div className="rail-cell">
          <span>추천 연결</span>
          <strong>{data.summary.recommended_stock_count.toLocaleString("ko-KR")}</strong>
          <small>추천/논리가 붙은 종목</small>
        </div>
        <div className="rail-cell">
          <span>보유 중</span>
          <strong>{data.summary.held_stock_count.toLocaleString("ko-KR")}</strong>
          <small>포트폴리오 스냅샷 기준</small>
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-2" aria-labelledby="stock-list-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">종목 목록</span>
            <h2 id="stock-list-title">수집된 주식</h2>
          </div>
          <Link className="btn btn-secondary" href="/data-health">
            데이터 수집 상태 보기
          </Link>
        </div>

        <div className="stock-table" role="table" aria-label="수집된 종목 목록">
          <div className="stock-table-row stock-table-head" role="row">
            <span role="columnheader">종목</span>
            <span role="columnheader">최신 가격</span>
            <span role="columnheader">가격일</span>
            <span role="columnheader">수집 길이</span>
            <span role="columnheader">추천 상태</span>
            <span role="columnheader">보유 비중</span>
          </div>
          {data.stocks.map((stock) => (
            <div className="stock-table-row" key={stock.symbol} role="row">
              <span role="cell">
                <Link className="stock-symbol-link" href={stockHref(stock.symbol)}>
                  <strong>{stock.symbol}</strong>
                  <small>{stock.name}</small>
                </Link>
              </span>
              <span role="cell">
                <strong>{formatCurrency(stock.latest_price.close, stock.currency_code)}</strong>
                <small>{formatPercent(stock.latest_price.change_pct)}</small>
              </span>
              <span role="cell">{stock.latest_price.trade_date || "없음"}</span>
              <span role="cell">
                {stock.data_coverage.bar_count.toLocaleString("ko-KR")}일
                <small>{stock.data_coverage.first_trade_date || "시작일 없음"}</small>
              </span>
              <span role="cell">
                {stock.recommendation ? koCode(stock.recommendation.action) : "추천 없음"}
                <small>{stock.recommendation?.as_of_date || "검토 전"}</small>
              </span>
              <span role="cell">
                {stock.position ? formatPercent(stock.position.weight) : "미보유"}
                <small>{stock.position ? koLabel(stock.position.portfolio_name) : "포트폴리오 없음"}</small>
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
