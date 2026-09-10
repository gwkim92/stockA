"use client";
import Link from "next/link";
import type { Route } from "next";
import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import { StatusBadge } from "@/components/status/StatusBadge";
import { label, object, linked, currency, finite, ratioLabel, numberLabel, dateLabel, count, scopesFor, stockSearchPath, type DiscoveryData, type StockSearch } from "@/lib/discovery-model";
import styles from "./DiscoveryWorkspace.module.css";
export function StockExplorer({ data, search = {} }: { data: DiscoveryData; search?: StockSearch }) {
  const reference = data.asOfDate, rows = data.rows;
  const scope = scopesFor("stocks").some(item => item.key === search.scope) ? search.scope! : "all";
  const summary = object(data.raw.summary);
  const counts: Record<string, unknown> = { all: data.raw.stock_count, recommended: summary.recommended_stock_count, held: summary.held_stock_count, attention: summary.attention_stock_count };
  return <section className={styles.panel} aria-label="종목 탐색 결과" data-testid="stock-explorer">
    <div className={styles.toolbar}>
      <nav className={styles.filters} aria-label="종목 조건">{scopesFor("stocks").map(item => <Link key={item.key} href={stockSearchPath({ q: search.q, scope: item.key }) as Route} aria-current={scope === item.key ? "page" : undefined}>{item.name}<span>{count(counts[item.key]) ?? "미확인"}</span></Link>)}</nav>
      <form className={styles.stockSearch} action="/stocks" key={`${search.q}-${scope}`} role="search" aria-label="전체 조회 대상 종목 검색">
        <input type="hidden" name="scope" value={scope} />
        <input aria-label="종목 검색" name="q" defaultValue={search.q ?? ""} maxLength={100} placeholder="기업명, 코드, 시장" />
        <button type="submit">검색</button>
      </form>
    </div>
    <p className={styles.resultCount} role="status">검색 결과 {count(data.raw.matched_stock_count) ?? "미확인"}개 · 이 페이지 {rows.length}개 <Link href="/stocks">필터 초기화</Link></p>
    <div className={styles.stockColumns} aria-hidden="true"><span>기업 / 시장</span><span>가격과 관측일</span><span>추천·보유 연결</span><span>리서치</span></div>
    {rows.map(row => { const p = object(row.latest_price), r = object(row.recommendation), h = object(row.position);
      const symbol = label(row.symbol), recommendation = linked(row, "recommendation"), held = linked(row, "position");
      return <article className={styles.stockRow} key={label(row.instrument_id)}>
        <header className={styles.identity}><span className={styles.monogram} aria-hidden="true">{symbol.slice(0, 1)}</span><div><Link href={`/stocks/${encodeURIComponent(symbol)}` as Route}>{symbol}</Link><h2>{label(row.name, symbol)}</h2><small>{label(row.market_code)} · {label(row.currency_code)}</small></div></header>
        <div className={styles.price}><span>기록된 종가</span><strong>{currency(p.close, row.currency_code)}</strong><SignedReturnBadge value={finite(p.change_pct)} /><small>{dateLabel(p.trade_date, reference)}</small></div>
        <div className={styles.connections}><StatusBadge kind={recommendation ? "watch" : "empty"} label={recommendation ? "추천 연결 · 근거 확인 필요" : row.recommendation === null ? "추천 연결 없음" : "추천 연결 미확인"} />
          {recommendation && <p>모델 점수 {numberLabel(r.score)} · {label(r.as_of_date, "추천일 미확인")}</p>}
          <p>{held ? `${label(h.portfolio_name)} · 비중 ${ratioLabel(h.weight)}` : row.position === null ? "보유 연결 없음" : "보유 연결 미확인"}</p>
          {held && <small>보유 기록 {label(h.snapshot_date, "기준일 미확인")}</small>}
        </div>
        <div className={styles.rowActions}><Link href={`/stocks/${encodeURIComponent(symbol)}` as Route} aria-label={`${symbol} 종목 분석 열기`}>종목 분석 →</Link>{recommendation && <Link href={`/recommendations/${encodeURIComponent(label(r.recommendation_id))}` as Route}>추천 판단서</Link>}</div>
      </article>;
    })}
    {!rows.length && <div className={styles.empty}><h2>조건에 맞는 결과가 없습니다</h2><p>조회 대상 전체에서 검색했습니다. 검색어나 필터를 바꿔보세요.</p><Link href="/stocks">조건 초기화</Link></div>}
    <nav className={styles.stockPagination} aria-label="종목 목록 페이지">
      {search.cursor && <Link href={stockSearchPath({ q: search.q, scope }) as Route}>처음 페이지</Link>}
      {data.nextCursor && <Link href={stockSearchPath({ q: search.q, scope, cursor: data.nextCursor }) as Route}>다음 종목</Link>}
    </nav>
    <p className={styles.footnote}>가격은 실시간 시세가 아닙니다. 추천 연결은 자료의 존재를 뜻하며, 근거 충족이나 매수 적합성을 확인한 결과가 아닙니다. 모델 점수는 수익률·성공 확률이 아닙니다.</p>
  </section>;
}
