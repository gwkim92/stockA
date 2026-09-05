import Link from "next/link";
import type { Route } from "next";
import type { ReactNode } from "react";
import type { DiscoveryResult } from "@/lib/discovery-data";
import { dateLabel } from "@/lib/discovery-model";
import styles from "./DiscoveryWorkspace.module.css";
export function DiscoveryFrame({ title, eyebrow, description, result, children }: { title: string; eyebrow: string; description: string; result: DiscoveryResult; children: ReactNode }) {
  return <div className={styles.page} data-testid="discovery-workspace">
    <header className={styles.heading}><div><span>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div></header>
    <nav className={styles.contextNav} aria-label="시장과 기업 탐색">
      {[["/market-map", "시장 배경"], ["/cycles", "테마 사이클"], ["/stocks", "종목 탐색"]].map(([href, name]) => <Link key={href} href={href as Route} aria-current={href === (result.data?.kind === "stocks" ? "/stocks" : result.data?.kind === "cycles" ? "/cycles" : result.data?.kind === "market" ? "/market-map" : null) ? "page" : undefined}>{name}</Link>)}
    </nav>
    {!result.data ? <section className={styles.empty} role="status"><h2>{result.issue === "timeout" ? "응답이 지연되고 있습니다" : "이 화면의 자료를 불러오지 못했습니다"}</h2><p>조회 실패를 데이터 0건이나 정상 상태로 표시하지 않습니다.</p><a href="">다시 조회</a><Link href="/">리서치 홈으로</Link></section>
      : <><p className={styles.dateContext}>분석 스냅샷 {dateLabel(result.data.asOfDate, result.requestedDate)}{result.data.partial ? " · 일부 결과" : ""}</p>{children}</>}
    <footer><Link className={styles.textLink} href="/recommendations">투자 후보 검토 →</Link></footer>
  </div>;
}
export function DiscoveryMetrics({ items }: { items: readonly { name: string; value: string; note: string }[] }) {
  return <div className={styles.metricBlock}>
    <dl className={styles.metrics}>{items.map(item => <div key={item.name}><dt>{item.name}</dt><dd>{item.value}</dd></div>)}</dl>
    <details className={styles.metricNotes}><summary>지표 집계·기준일 안내</summary>
      <p>개별 가격·원천의 관측일은 각 항목에 표시합니다. 화면 조회 시각은 데이터 최신성을 뜻하지 않습니다.</p>
      <dl>{items.map(item => <div key={item.name}><dt>{item.name}</dt><dd>{item.note}</dd></div>)}</dl>
    </details>
  </div>;
}
