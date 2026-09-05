"use client";
import Link from "next/link";
import type { Route } from "next";
import { koCode, koLabel } from "@/lib/korean-labels";
import { StatusBadge } from "@/components/status/StatusBadge";
import { changedCycle, count, cycleGap, FEATURE_KEYS, filterDiscovery, fraction, label, object, ratioLabel, validState, type DiscoveryData } from "@/lib/discovery-model";
import { DiscoveryToolbar, EmptyDiscovery, useDiscoveryQuery } from "./DiscoveryControls";
import styles from "./DiscoveryWorkspace.module.css";
const names = { event_intensity: "뉴스 특징", price_momentum: "가격 특징", fundamental_quality: "기업 품질 특징" };
export function CycleExplorer({ data }: { data: DiscoveryData }) {
  const control = useDiscoveryQuery("cycles");
  const rows = filterDiscovery(data.rows, "cycles", control.query, control.scope, "", data.asOfDate);
  const counts = Object.fromEntries(control.scopes.map(item => [item.key, filterDiscovery(data.rows, "cycles", "", item.key, "", data.asOfDate).length]));
  return <section className={styles.panel} aria-label="테마 사이클 탐색" data-testid="cycle-explorer">
    <DiscoveryToolbar kind="cycles" control={control} counts={counts} total={data.rows.length} shown={rows.length} />
    <div className={styles.cycleGrid}>{rows.map(row => {
      const before = validState(row.previous_state), after = validState(row.state), key = label(row.theme_key);
      return <article key={key} className={styles.cycleCard}>
        <header><div><span className={styles.kicker}>{key}</span><h2>{koLabel(label(row.theme_name, koCode(key)))}</h2></div><StatusBadge kind={changedCycle(row) ? "watch" : "empty"} label={!before || !after ? "상태 비교 미확인" : changedCycle(row) ? "전환 관측" : "상태 유지"} /></header>
        <p className={styles.transition}>{before ? koCode(before) : "이전 상태 미확인"}<span aria-hidden="true"> → </span>{after ? koCode(after) : "현재 상태 미확인"}</p>
        <div className={styles.featureList}>{FEATURE_KEYS.map(feature => { const value = fraction(object(row.features)[feature]); return <div key={feature}><span>{names[feature]}</span><div className={styles.track} aria-hidden="true">{value !== null && <i style={{ width: `${value * 100}%` }} />}</div><strong>{ratioLabel(value)}</strong></div>; })}</div>
        <p className={styles.note}>특징 값은 정규화된 모델 입력이며 실제 수익률이 아닙니다.{cycleGap(row) ? " 미측정 축을 0으로 채우지 않습니다." : ""}</p>
        <dl className={styles.inlineFacts}><div><dt>모델 신뢰도</dt><dd>{ratioLabel(row.confidence)}</dd></div><div><dt>테마 연결</dt><dd>{count(row.instrument_count) ?? "미확인"}개</dd></div></dl>
        <div className={styles.symbols}>{(Array.isArray(row.top_symbols) ? row.top_symbols : []).filter((s): s is string => typeof s === "string" && !!s.trim()).slice(0, 6).map((symbol, index) => <Link key={`${symbol}-${index}`} href={`/stocks/${encodeURIComponent(symbol)}` as Route}>{symbol}</Link>)}</div>
        <Link className={styles.textLink} href={`/themes/${encodeURIComponent(key)}` as Route}>테마 근거와 연결 기업 →</Link>
      </article>;
    })}</div>
    {!rows.length && <EmptyDiscovery hasRows={data.rows.length > 0} reset={control.reset} />}
    <p className={styles.footnote}>이전·현재 상태가 모두 있을 때만 전환으로 집계합니다. 전환은 가격 상승·매수 신호가 아니며, 같은 종목이 여러 테마에 포함될 수 있습니다.</p>
  </section>;
}
