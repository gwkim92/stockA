"use client";
import Link from "next/link";
import type { Route } from "next";
import { koCode } from "@/lib/korean-labels";
import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import { StatusBadge } from "@/components/status/StatusBadge";
import { filterHoldings, money, weight, type Holding } from "@/lib/review-workspace-model";
import { HOLDING_FILTERS, ReviewFilters, useReviewFilters } from "./ReviewFilters";
import styles from "./ReviewWorkspace.module.css";
export function HoldingsReview({ rows }: { rows: readonly Holding[] }) {
  const controls = useReviewFilters(), filtered = filterHoldings(rows, controls.query, controls.scope);
  return <section className={styles.panel} aria-label="보유 종목 검토" data-testid="holdings-review">
    <div className={styles.panelHeading}><h2>보유 종목과 검토 사유</h2><p>평가손익과 투자 논리의 상태는 서로 다릅니다. 수익이 났다는 이유로 보유 근거를 충족했다고 보지 않습니다.</p></div>
    <ReviewFilters controls={controls} filters={HOLDING_FILTERS} shown={filtered.length} total={rows.length} />
    {filtered.map(row => <article key={row.id} className={styles.holding}>
      <div className={styles.identity}><Link href={`/stocks/${encodeURIComponent(row.symbol)}` as Route}>{row.symbol}</Link><span>보유 비중 {weight(row.weight)}</span><StatusBadge kind={row.thesisState === "linked" ? "watch" : "source_limited"} label={row.thesisState === "linked" ? "투자 논리 연결" : row.thesisState === "missing" ? "투자 논리 누락" : "투자 논리 미확인"} /></div>
      <div className={styles.holdingFacts}><dl><div><dt>기록 평가액</dt><dd>{money(row.market, row.currency)}</dd></div><div><dt>평가손익</dt><dd>{money(row.pnl, row.currency)}</dd></div></dl><SignedReturnBadge value={row.returnPct} label="평가손익률" options={{ metricLabel: `${row.symbol} 평가손익률`, upLabel: "수익", downLabel: "손실" }} /><small>{row.amountVerified ? `${row.currency} 환산 필드 기준 · 현금흐름 수익률 아님` : "원가·평가액·기준통화 확인 전 · 합계 제외"}</small></div>
      <div className={styles.reviewReason}><h3>{koCode(row.action)}</h3><p>성과 기록: {koCode(row.outcome)}</p><p>보유 크기: {koCode(row.sizeStatus)}</p>{row.sizeNote && <p>{row.sizeNote}</p>}<div className={styles.links}><Link href={`/stocks/${encodeURIComponent(row.symbol)}` as Route}>기업 분석 →</Link>{row.thesisId && <Link href={`/theses/${encodeURIComponent(row.thesisId)}` as Route}>투자 논리 →</Link>}</div></div>
    </article>)}
    {!filtered.length && <div className={styles.empty}><h3>{rows.length ? "조건에 맞는 보유 종목이 없습니다" : "수신된 보유 목록이 비어 있습니다"}</h3><p>{rows.length ? "다른 조건으로 비교하세요. 원래 목록의 순서는 바꾸지 않습니다." : "이 결과만으로 실제 계좌가 비었다고 단정하지 않습니다."}</p></div>}
  </section>;
}
