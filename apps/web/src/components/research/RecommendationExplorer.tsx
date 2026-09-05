"use client";
import { useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { WorkspaceIcon } from "@/components/shell/WorkspaceIcon";
import { StatusBadge } from "@/components/status/StatusBadge";
import { koCode } from "@/lib/korean-labels";
import { filterRecommendations, sourceLimited, researchScore, type ExplorerFilter, type ExplorerRow } from "@/lib/recommendation-explorer-model";
import styles from "./RecommendationExplorer.module.css";
export function RecommendationExplorer({ rows }: { readonly rows: readonly ExplorerRow[] }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<ExplorerFilter>("all");
  const result = filterRecommendations(rows, query, filter);
  const tabs: readonly { key: ExplorerFilter; label: string }[] = [{ key: "all", label: "전체 후보" }, { key: "linked", label: "논리 연결" }, { key: "limited", label: "원천 제한" }];
  return <section className={styles.explorer} aria-labelledby="explorer-title" data-testid="recommendation-explorer">
    <header className={styles.heading}><div><h2 id="explorer-title">투자 후보 탐색</h2><p>기업과 근거를 비교하고, 판단서를 읽어보세요.</p></div><span>백엔드 순위 유지</span></header>
    <div className={styles.toolbar}><div className={styles.filters} aria-label="후보 조건">{tabs.map(tab => <button type="button" key={tab.key} aria-pressed={filter === tab.key} onClick={() => setFilter(tab.key)}>{tab.label}<span>{filterRecommendations(rows, "", tab.key).length}</span></button>)}</div>
      <label className={styles.search}><WorkspaceIcon name="search" /><input aria-label="투자 후보 이름 또는 종목 코드" placeholder="기업명 또는 종목 코드" value={query} onChange={event => setQuery(event.target.value)} /></label>
    </div>
    <p className={styles.resultCount} role="status">수신된 {rows.length}개 중 {result.length}개 표시 · 점수는 예상 수익률이나 성공 확률이 아닙니다.</p>
    <div className={styles.columnHead} aria-hidden="true"><span>기업 / 순위</span><span>모델 점수</span><span>연결 근거와 판단 상태</span><span>판단서</span></div>
    <div className={styles.rows}>{result.map(row => <article key={row.recommendation_id} className={styles.row}>
      <div className={styles.identity}><span className={styles.monogram} aria-hidden="true">{row.symbol.slice(0,1)}</span><div><Link href={`/stocks/${encodeURIComponent(row.symbol)}` as Route}><strong>{row.symbol}</strong></Link><span>{row.name}</span><small>기록 순위 {row.rank_position > 0 ? row.rank_position : "미확인"}</small></div></div>
      <div className={styles.score}><small>모델 점수</small><strong>{researchScore(row.score)}</strong></div>
      <div className={styles.evidence}><StatusBadge kind={sourceLimited(row) ? "source_limited" : row.linked_thesis_id ? "watch" : "empty"} label={sourceLimited(row) ? "원천 제한" : row.linked_thesis_id ? "투자 논리 연결" : "논리 확인 필요"} /><strong>{row.evidence_quality.title || "상세 근거 확인"}</strong><p>{row.evidence_quality.missing_layer_labels.length ? `보강 필요: ${row.evidence_quality.missing_layer_labels.slice(0,2).map(koCode).join(", ")}` : "원문과 무효화 조건을 함께 확인하세요."}</p></div>
      <Link className={styles.open} href={`/recommendations/${encodeURIComponent(row.recommendation_id)}` as Route} aria-label={`${row.symbol} 투자 판단서 열기`}>판단서 <WorkspaceIcon name="arrow" /></Link>
    </article>)}</div>
    {!result.length && <div className={styles.empty}><WorkspaceIcon name="search" /><h3>{rows.length ? "조건에 맞는 후보가 없습니다" : "수신된 투자 후보가 없습니다"}</h3><p>{rows.length ? "다른 기업명으로 검색하거나 필터를 초기화하세요." : "후보가 없는 상태와 분석되지 않은 상태는 다릅니다. 데이터 상태를 확인하세요."}</p>{rows.length ? <button type="button" onClick={() => { setQuery(""); setFilter("all"); }}>필터 초기화</button> : <Link href="/data-health">데이터 상태 확인</Link>}</div>}
  </section>;
}
