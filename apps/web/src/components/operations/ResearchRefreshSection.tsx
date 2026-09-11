"use client";

import { useState } from "react";
import { refreshStates, refreshTime, type ResearchRefreshStatus } from "@/lib/research-refresh";
import styles from "./ResearchRefreshSection.module.css";

export function ResearchRefreshSection({ data }: { data?: ResearchRefreshStatus }) {
  const [filter, setFilter] = useState("all");
  const [query, setQuery] = useState("");
  const unavailable = !data || data.status === "unavailable";
  const rows = (data?.rows ?? []).filter(row => (filter === "all" || row.state === filter)
    && row.symbol.toLowerCase().includes(query.trim().toLowerCase()));
  return <section className={`feature-map-panel ${styles.panel}`} id="research-refresh" aria-labelledby="research-refresh-title">
    <div className={styles.heading}>
      <div><span className={styles.eyebrow}>기업 리서치 자동화</span><h2 id="research-refresh-title">보고서 갱신 현황</h2></div>
      <a className="text-link" href="/admin/ai-agents">AI 모델 설정 →</a>
    </div>
    {unavailable ? <p role="status">갱신 현황을 불러오지 못했습니다. 대기 건수와 한도 사용량은 확인되지 않았습니다.</p> : <>
      <p className={styles.intro}>재무 자료가 바뀌면 보고서를 다시 생성합니다. 한 번에 1개씩, 하루 {data.daily_limit}회 한도 안에서 처리합니다.</p>
      <dl className={styles.metrics}>
        <div><dt>생성 대기</dt><dd>{data.counts.due ?? 0}<small>개</small></dd></div>
        <div><dt>원천 자료 대기</dt><dd>{data.counts.waiting_for_source ?? 0}<small>개</small></dd></div>
        <div><dt>실행·결과 확인</dt><dd>{data.attention_count}<small>개</small></dd></div>
        <div><dt>오늘 생성 한도 사용</dt><dd>{data.daily_used}<small> / {data.daily_limit}회</small></dd></div>
      </dl>
      <div className={styles.budget}>
        <span>{data.daily_remaining === 0 ? "오늘 한도 소진 · 다음 한도 초기화 후 자동 실행을 기다립니다." : `오늘 남은 한도 ${data.daily_remaining}회`}</span>
        <span>한도 초기화 {refreshTime(data.budget_resets_at)} KST · UTC 날짜 기준</span>
      </div>
      <p className={styles.meta}>설정 모델 <strong>{data.model_name ?? "확인 불가"}</strong> · 재무 버전 일치 {data.counts.current ?? 0}개 · 재시도 대기 {data.counts.retry_wait ?? 0}개 · 조회 {refreshTime(data.observed_at)} KST</p>
      <details className={styles.details} open={Boolean(data.attention_count)}>
        <summary>기업별 상태와 처리 이유 <span>{data.total_count}개</span></summary>
        <div className={styles.filters}>
          <label>기업 찾기<input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="종목 코드" /></label>
          <label>상태<select value={filter} onChange={event => setFilter(event.target.value)}>
            <option value="all">전체</option>
            {Object.entries(refreshStates).filter(([key]) => data.counts[key]).map(([key, state]) => <option key={key} value={key}>{state.label} ({data.counts[key]})</option>)}
          </select></label>
        </div>
        <p className={styles.meta} aria-live="polite">{rows.length}개 기업</p>
        <ul className={styles.rows}>
          {rows.map(row => {
            const state = refreshStates[row.state] ?? refreshStates.unknown;
            return <li key={row.symbol}>
              <div className={styles.rowHeading}><a href={`/stocks/${encodeURIComponent(row.symbol)}`}>{row.symbol}</a><span className={state.attention ? styles.attention : styles.state}>{state.label}</span></div>
              <p>{row.state === "due" && data.daily_remaining === 0 ? "오늘 한도를 모두 사용했습니다. 다음 한도 초기화 후 자동 실행에서 처리합니다." : state.detail}</p>
              <small>재무 수집 {refreshTime(row.source_collected_at)}{row.retry_after ? ` · 재시도 가능 ${refreshTime(row.retry_after)} KST` : ""}{row.claim_id ? ` · 실행 기록 #${row.claim_id}` : ""}</small>
            </li>;
          })}
        </ul>
        {rows.length === 0 ? <p>{data.total_count === 0 ? "현재 자동 갱신 대상 기업이 없습니다." : "조건에 맞는 기업이 없습니다."}</p> : null}
      </details>
      <p className={styles.footnote}>재무 버전 일치는 보고서가 사용한 재무 자료의 일치를 뜻합니다. 뉴스·가격 전체의 최신성이나 내용의 정확성을 보증하지 않습니다. 한도 사용량에는 예약과 기존 수동 생성 기록이 포함됩니다.</p>
    </>}
  </section>;
}
