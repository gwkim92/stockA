"use client";
import Link from "next/link";
import type { Route } from "next";
import { useSearchParams } from "next/navigation";
import { koCode } from "@/lib/korean-labels";
import { filterHoldings, money, percent, weight, type Holding } from "@/lib/review-workspace-model";
import { HOLDING_FILTERS, ReviewFilters, useReviewFilters } from "./ReviewFilters";
import styles from "./HoldingsTable.module.css";
const thesisLabel = (row: Holding) => row.thesisState === "linked" ? "투자 논리 연결" : row.thesisState === "missing" ? "투자 논리 누락" : "투자 논리 미확인";
export function HoldingsReview({ rows }: { rows: readonly Holding[] }) {
  const controls = useReviewFilters(), params = useSearchParams();
  const filtered = filterHoldings(rows, controls.query, controls.scope);
  const selected = filtered.find(row => row.id === params.get("holding")) ?? filtered[0];
  return <section className={styles.panel} aria-label="보유 종목 검토" data-testid="holdings-review">
    <header className={styles.heading}><h2>보유 종목과 검토 사유</h2><p>종목을 선택해 검토 기록을 읽습니다.</p></header>
    <ReviewFilters controls={controls} filters={HOLDING_FILTERS} shown={filtered.length} total={rows.length} />
    <div className={styles.workbench}>
      <div className={styles.tableScroll} tabIndex={0} role="region" aria-label="보유 비교 표 · 가로 스크롤 가능"><table><caption>보고된 보유 순서 · 목록 필터는 상단 소계에 영향을 주지 않습니다.</caption><thead><tr><th scope="col">종목</th><th scope="col">비중</th><th scope="col">기록 평가액</th><th scope="col">평가손익</th><th scope="col">평가손익률</th><th scope="col">논리 상태</th></tr></thead><tbody>
        {filtered.map(row => <tr key={row.id} data-selected={row.id === selected?.id}><th scope="row"><button type="button" aria-label={`${row.symbol} 검토 선택`} aria-pressed={row.id === selected?.id} onClick={() => controls.update({ holding: row.id }, true)}>{row.symbol} <span aria-hidden="true">↗</span></button></th><td>{weight(row.weight)}</td><td>{money(row.market, row.currency)}</td><td data-tone={row.pnl === null ? "unknown" : row.pnl < 0 ? "negative" : row.pnl > 0 ? "positive" : "neutral"}>{money(row.pnl, row.currency)}</td><td data-tone={row.returnPct === null ? "unknown" : row.returnPct < 0 ? "negative" : row.returnPct > 0 ? "positive" : "neutral"}>{percent(row.returnPct)}</td><td>{thesisLabel(row)}</td></tr>)}
      </tbody></table>{!filtered.length && <div className={styles.empty}><h3>{rows.length ? "조건에 맞는 보유 종목이 없습니다" : "수신된 보유 목록이 비어 있습니다"}</h3><p>{rows.length ? "다른 조건으로 비교하세요. 원래 목록의 순서는 바꾸지 않습니다." : "이 결과만으로 실제 계좌가 비었다고 단정하지 않습니다."}</p></div>}</div>
      {selected && <aside className={styles.detail} aria-label="선택한 보유 종목 검토"><span>검토 맥락</span><h3>{selected.symbol}</h3><p className={styles.thesis}>{thesisLabel(selected)}</p><h4>{koCode(selected.action)}</h4><dl><div><dt>성과 기록</dt><dd>{koCode(selected.outcome)}</dd></div><div><dt>보유 크기</dt><dd>{selected.sizeStatus === "within_limit" ? "설정 한도 내" : koCode(selected.sizeStatus)}</dd></div></dl>{selected.sizeNote && <p>{selected.sizeNote}</p>}<p className={styles.note}>{selected.amountVerified ? `${selected.currency} 환산 필드 기준 · 현금흐름 수익률 아님` : "원가·평가액·기준통화 확인 전 · 합계 제외"}</p><nav aria-label="보유 종목 연결"><Link href={`/stocks/${encodeURIComponent(selected.symbol)}` as Route}>기업 분석 →</Link>{selected.thesisId && <Link href={`/theses/${encodeURIComponent(selected.thesisId)}` as Route}>투자 논리 →</Link>}<Link href={`/performance/recommendations?symbol=${encodeURIComponent(selected.symbol)}` as Route}>성과 기록 →</Link></nav></aside>}
    </div>
    <p className={styles.note}>평가손익과 투자 논리의 상태는 다릅니다. 수익이 났다는 이유로 보유 근거가 충족됐다고 보지 않습니다.</p>
  </section>;
}
