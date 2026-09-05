"use client";
import Link from "next/link";
import type { Route } from "next";
import { koCode } from "@/lib/korean-labels";
import { StatusBadge } from "@/components/status/StatusBadge";
import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import { filterDiscovery, finite, flattenMarket, label, marketAttention, numberLabel, object, objectRows, ratioLabel, safeSource, type DiscoveryData } from "@/lib/discovery-model";
import { DiscoveryToolbar, EmptyDiscovery, useDiscoveryQuery } from "./DiscoveryControls";
import styles from "./DiscoveryWorkspace.module.css";
export function MarketExplorer({ data, requestedDate }: { data: DiscoveryData; requestedDate: string }) {
  const control = useDiscoveryQuery("market"), all = flattenMarket(data.rows);
  const rows = filterDiscovery(all, "market", control.query, control.scope, control.group, requestedDate);
  const counts = Object.fromEntries(control.scopes.map(item => [item.key, filterDiscovery(all, "market", "", item.key, "", requestedDate).length]));
  return <section className={styles.panel} aria-label="시장 지표 탐색" data-testid="market-explorer">
    <DiscoveryToolbar kind="market" control={control} counts={counts} total={all.length} shown={rows.length}>
      <label>시장 영역<select aria-label="시장 영역" value={control.group} onChange={e => control.update({ group: e.target.value }, true)}><option value="">모든 영역</option>{data.rows.map(group => <option key={label(group.group_code)} value={label(group.group_code)}>{label(group.group_name, label(group.group_code))}</option>)}</select></label>
      <label>변화율 기간<select aria-label="변화율 기간" value={control.window} onChange={e => control.update({ window: e.target.value }, true)}>{["1d", "5d", "20d", "60d"].map(window => <option key={window} value={window}>{window.slice(0, -1)}일</option>)}</select></label>
      <span>기간별 변화율은 동일 단위 자산의 가격 수준 비교가 아닙니다.</span>
    </DiscoveryToolbar>
    <div className={styles.marketGrid}>{rows.map(row => {
      const attention = marketAttention(row, requestedDate), code = label(row.indicator_code);
      const source = object(row.source_policy);
      return <article key={`${row.group_code}-${code}`} className={styles.indicator}>
        <header><span className={styles.kicker}>{label(row.group_name)} / {code}</span><StatusBadge kind={attention ? "source_limited" : "watch"} label={attention ? "원천 확인 필요" : "원천 판정: 최신"} /></header>
        <h2>{label(row.display_name, code)}</h2>
        <div className={styles.indicatorValue}><div><small>기록된 지표값 · 고유 단위</small><strong>{numberLabel(row.latest_value)}</strong></div><SignedReturnBadge value={finite(row[`return_${control.window}`])} label={`${control.window.slice(0, -1)}일 변화`} options={{ metricLabel: `${control.window.slice(0, -1)}일 변화` }} /></div>
        <p className={styles.note}>관측일 {label(row.latest_observation_date, "미확인")} · {koCode(label(row.preferred_provider))}</p>
        {code === "XAG_USD" && <p className={styles.warning}>은 현물 가격이 아닌 프록시 지수입니다. 방향성 보조 자료로만 비교하세요.</p>}
        <p className={styles.note}>{label(row.quality_note_ko, label(row.note_ko, "원천 설명 미제공"))}</p>
        <details className={styles.details}><summary>지표 특징·원천 정책</summary><dl className={styles.sourceFacts}>
          <div><dt>원천 심볼</dt><dd>{label(row.provider_symbol)}</dd></div><div><dt>원천 최신성 판정</dt><dd>{koCode(label(row.freshness_status))}</dd></div>
          <div><dt>1 / 5 / 20 / 60일 변화</dt><dd>{["1d", "5d", "20d", "60d"].map(window => <span key={window}>{window}: {finite(row[`return_${window}`]) === null ? "미측정" : `${numberLabel(Number(row[`return_${window}`]) * 100)}%`} </span>)}</dd></div>
          <div><dt>252일 위치 / Z-score</dt><dd>{ratioLabel(row.percentile_252d)} / {numberLabel(row.z_score_252d)}</dd></div>
          <div><dt>추세 / 충격 방향</dt><dd>{koCode(label(row.trend_state))} / {koCode(label(row.shock_direction))}</dd></div>
          <div><dt>원천·이용 조건</dt><dd>{label(source.license_note, "미제공")}</dd></div><div><dt>재배포 조건</dt><dd>{label(source.redistribution_allowed_note, "미제공")}</dd></div>
          <div><dt>지연 처리 정책</dt><dd>{label(row.stale_policy, "미제공")}</dd></div>
        </dl></details>
      </article>;
    })}</div>
    {!rows.length && <EmptyDiscovery hasRows={all.length > 0} reset={control.reset} />}
    <p className={styles.footnote}>관측일과 제공 원천의 품질 판정을 함께 확인하세요. 최신성 임계값이나 추천 가중치를 이 화면에서 변경하지 않습니다.</p>
  </section>;
}
export function MarketEvidence({ data }: { data: DiscoveryData }) {
  const regimes = objectRows(data.raw.regimes), correlations = objectRows(data.raw.correlations), news = objectRows(data.raw.news_links), flags = objectRows(data.raw.quality_flags);
  return <div className={styles.evidenceSections}>
    <section className={styles.panel} aria-labelledby="market-regimes-title"><header className={styles.sectionHead}><span>모델 해석</span><h2 id="market-regimes-title">시장 체제와 상충 근거</h2><p>지표와 별도로 읽는 모델 출력입니다. 신호가 존재한다고 투자 판단이 검증된 것은 아닙니다.</p></header>
      <div className={styles.regimeGrid}>{regimes.map((row, i) => <article key={`${row.regime_code}-${i}`} className={styles.evidenceCard}><StatusBadge kind="watch" label={koCode(label(row.regime_state))} /><h3>{koCode(label(row.regime_code))}</h3><p>{label(row.summary_ko, "해석 미제공")}</p><small>모델 점수 {numberLabel(row.regime_score)} · 신뢰도 {ratioLabel(row.confidence)}</small><p className={styles.note}>구성 지표 {(Array.isArray(row.driver_indicator_codes) ? row.driver_indicator_codes : []).map(v => label(v)).join(" · ") || "미확인"}</p>{Array.isArray(row.conflict_flags) && row.conflict_flags.length > 0 && <p className={styles.warning}>상충 기록: {row.conflict_flags.map(v => koCode(label(v))).join(" · ")}</p>}</article>)}</div>
      {!regimes.length && <p className={styles.emptyText}>{data.raw.regimes == null ? "시장 체제 자료 미제공" : "기록된 시장 체제가 없습니다."}</p>}
    </section>
    <section className={styles.panel} aria-labelledby="market-correlation-title"><header className={styles.sectionHead}><span>동조성</span><h2 id="market-correlation-title">종목과 시장은 어떻게 같이 움직였나</h2><p>상관관계는 인과관계나 매수·매도 이유를 뜻하지 않습니다. 관측 기간·표본 수를 함께 비교하세요.</p></header>
      {correlations.length > 0 ? <div className={styles.tableScroll} role="region" aria-label="상관관계 표 가로 스크롤" tabIndex={0}><table><caption>저장된 상관관계 · 원래 반환 순서</caption><thead><tr><th scope="col">비교 쌍</th><th scope="col">기준일 / 기간</th><th scope="col">상관계수</th><th scope="col">베타</th><th scope="col">관측 수</th></tr></thead><tbody>{correlations.map((row, i) => <tr key={i}><th scope="row">{label(row.primary_display_name)} ↔ {label(row.comparison_display_name)}<small>{label(row.summary_ko, "해석 미제공")}</small></th><td>{label(row.as_of_date)}<small>{numberLabel(row.lookback_days, 0)}일</small></td><td>{numberLabel(row.correlation)}</td><td>{numberLabel(row.beta)}</td><td>{numberLabel(row.observation_count, 0)}</td></tr>)}</tbody></table></div> : <p className={styles.emptyText}>{data.raw.correlations == null ? "상관관계 자료 미제공" : "저장된 상관관계가 없습니다."}</p>}
    </section>
    <div className={styles.regimeGrid}>
      <section className={styles.panel}><header className={styles.sectionHead}><h2>연결된 뉴스 근거</h2><p>동시 관찰 기록이며 원인을 확정하지 않습니다.</p></header>{news.map((row, i) => {
        const url = safeSource(row.source_url), document = label(row.document_id, "");
        return <article key={i} className={styles.newsItem}><span className={styles.kicker}>{label(row.indicator_name)} · {label(row.link_date)}</span><h3>{label(row.title_ko, "제목 미제공")}</h3><p>{label(row.rationale, "연결 설명 미제공")}</p><small>{label(row.source_name, "원천 미표기")} · 신뢰도 {ratioLabel(row.confidence)}</small><div className={styles.rowActions}>{document && <Link href={`/source-documents/${encodeURIComponent(document)}` as Route}>저장 원문</Link>}{url && <a href={url} target="_blank" rel="noopener noreferrer">원문 출처 ↗</a>}</div></article>;
      })}{!news.length && <p className={styles.emptyText}>{data.raw.news_links == null ? "뉴스 연결 자료 미제공" : "연결된 뉴스 기록이 없습니다."}</p>}</section>
      <section className={styles.panel}><header className={styles.sectionHead}><h2>원천 품질 기록</h2><p>문제 기록이 없다는 것만으로 전체 원천이 정상이라고 보지 않습니다.</p></header>{flags.map((row, i) => <article key={i} className={styles.newsItem}><h3>{label(row.display_name, label(row.indicator_code))}</h3><small>{koCode(label(row.severity))} · {label(row.latest_observation_date, "관측일 미확인")}</small><p>{label(row.message_ko, "내용 미제공")}</p></article>)}{!flags.length && <p className={styles.emptyText}>{data.raw.quality_flags == null ? "품질 기록 미제공" : "제공된 품질 경고 목록이 비어 있습니다."}</p>}<Link className={styles.textLink} href="/data-health">수집·분석 상태 →</Link></section>
    </div>
  </div>;
}
