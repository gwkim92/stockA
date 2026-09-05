"use client";
import Link from "next/link";
import type { Route } from "next";
import { koCode } from "@/lib/korean-labels";
import { filterOutcomes, percent, type Outcome } from "@/lib/review-workspace-model";
import { OUTCOME_FILTERS, ReviewFilters, useReviewFilters } from "./ReviewFilters";
import styles from "./ReviewWorkspace.module.css";
export function OutcomeExplorer({ rows, benchmark }: { rows: readonly Outcome[]; benchmark: string }) {
  const controls = useReviewFilters();
  const horizons = [...new Set(rows.map(row => row.horizon))].sort((a, b) => (a ?? Infinity) - (b ?? Infinity));
  const horizon = horizons.some(h => String(h ?? "unknown") === controls.horizon) ? controls.horizon : "";
  const filtered = filterOutcomes(rows, controls.query, controls.scope, horizon);
  return <section className={styles.panel} aria-label="추천별 측정 결과" data-testid="outcome-explorer">
    <div className={styles.panelHeading}><h2>추천별 측정 결과</h2><p>관찰 기간이 다른 결과를 분리해 보세요. 목록 필터는 위 보고서 요약값을 다시 계산하지 않습니다.</p></div>
    <ReviewFilters controls={controls} filters={OUTCOME_FILTERS} total={rows.length} shown={filtered.length}><label className={styles.horizon}>관찰 기간<select aria-label="관찰 기간" value={horizon} onChange={e => controls.update({ horizon: e.target.value }, true)}><option value="">전체 기간</option>{horizons.map(h => <option key={h ?? "unknown"} value={h ?? "unknown"}>{h === null ? "기간 미확인" : `${h}일`}</option>)}</select></label></ReviewFilters>
    {filtered.map(row => <article className={styles.outcome} key={row.id}>
      <div className={styles.identity}><Link href={`/stocks/${encodeURIComponent(row.symbol)}` as Route}>{row.symbol}</Link><span>{row.horizon === null ? "관찰 기간 미확인" : `${row.horizon}일 관찰`} · {koCode(row.action)}</span><small>{koCode(row.result)}</small><div className={styles.links}>{row.recommendationId && <Link href={`/recommendations/${encodeURIComponent(row.recommendationId)}` as Route}>당시 추천 →</Link>}{row.thesisId && <Link href={`/theses/${encodeURIComponent(row.thesisId)}` as Route}>연결 투자 논리 →</Link>}</div></div>
      <dl className={styles.returnComparison}><div><dt>절대수익률</dt><dd>{percent(row.absolute)}</dd></div><div><dt>벤치마크 · {benchmark}</dt><dd>{percent(row.benchmark)}</dd></div></dl>
      <div className={styles.alpha} data-tone={row.alpha === null ? "unknown" : row.alpha > 0 ? "positive" : row.alpha < 0 ? "negative" : "flat"}><span>벤치마크 초과수익</span><strong>{percent(row.alpha, true)}</strong><small>종목 관점 기여 {row.contribution === null ? "미측정" : `${row.contribution.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}bp`}</small></div>
    </article>)}
    {!filtered.length && <div className={styles.empty}><h3>{rows.length ? "조건에 맞는 성과가 없습니다" : "수신된 측정 결과가 없습니다"}</h3><p>측정 대기·자료 누락과 수익률 0은 다른 상태입니다.</p></div>}
  </section>;
}
