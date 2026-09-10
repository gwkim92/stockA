"use client";
import Link from "next/link";
import type { Route } from "next";
import { useEffect, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { SourcePeek } from "./SourcePeek";
import styles from "./NewsWorkspace.module.css";
export type NewsItem = {
  id: string; kind: "event" | "cluster"; title: string; original: string; summary: string | null;
  date: string; subject: string; symbols: string[]; direction: string; risk: boolean;
  evidenceHref: string | null; sources: { id: string; title: string }[];
  reasons: string[]; notes: string[]; provider: string; model: string;
  confidence: string; quality: string; count: string; headlines: { title: string; date: string; direction: string }[];
};
export function NewsWorkspace({ items }: { items: NewsItem[] }) {
  const params = useSearchParams(), path = usePathname(), heading = useRef<HTMLHeadingElement>(null);
  const query = (params.get("q") ?? "").slice(0, 100), scope = params.get("scope") ?? "all", selectedId = params.get("item");
  const filtered = items.filter(item => (scope === "event" || scope === "cluster" ? item.kind === scope : scope === "risk" ? item.risk : true)
    && [item.title, item.original, item.subject, ...item.symbols].join(" ").toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()));
  const selected = filtered.find(item => item.id === selectedId) ?? filtered[0];
  function update(values: Record<string, string>, push = false) {
    const next = new URLSearchParams(window.location.search);
    for (const [key, value] of Object.entries(values)) { if (value && value !== "all") next.set(key, value); else next.delete(key); }
    window.history[push ? "pushState" : "replaceState"](null, "", `${path}${next.size ? `?${next}` : ""}`);
  }
  useEffect(() => { if (selectedId && window.matchMedia("(max-width: 760px)").matches) heading.current?.focus(); }, [selectedId]);
  return <section className={styles.workspace} aria-label="뉴스 목록과 선택한 근거" data-testid="news-workspace">
    <div className={styles.toolbar}>
      <div className={styles.filters} role="group" aria-label="뉴스 분류">{[["all", "전체"], ["event", "개별 뉴스"], ["cluster", "뉴스 묶음"], ["risk", "위험 검토"]].map(([key, label]) => <button key={key} type="button" aria-pressed={scope === key || (key === "all" && !["event", "cluster", "risk"].includes(scope))} onClick={() => update({ scope: key, item: "" }, true)}>{label}</button>)}</div>
      <label className={styles.search}>뉴스 검색<input type="search" value={query} maxLength={100} placeholder="제목 · 종목 · 테마" onChange={event => update({ q: event.target.value, item: "" })} /></label>
      <span className={styles.result} role="status">수신 {items.length}개 중 {filtered.length}개</span>
    </div>
    <div className={styles.split} data-open={Boolean(selectedId && selected)}>
      <div className={styles.list} aria-label="뉴스 선택 목록">
        <div className={styles.listLabel}>수신 순서 · 개별 뉴스 다음 묶음</div>
        {filtered.map(item => <button type="button" key={item.id} id={`news-${encodeURIComponent(item.id)}`} className={styles.row} aria-current={selected?.id === item.id ? "true" : undefined} onClick={() => update({ item: item.id }, true)}>
          <span className={styles.rowMeta}><span>{item.kind === "cluster" ? "묶음" : "뉴스"} · {item.subject}</span><time>{item.date}</time></span>
          <strong>{item.title}</strong><span className={styles.rowFoot}><span>{item.symbols.join(" · ") || "시장·테마"}</span><span data-risk={item.kind === "event" && item.risk}>{item.direction}</span></span>
        </button>)}
        {!filtered.length && <div className={styles.empty}><h2>조건에 맞는 뉴스가 없습니다</h2><p>검색은 현재 수신된 목록에 적용됩니다.</p><button type="button" onClick={() => update({ q: "", scope: "all", item: "" })}>검색·필터 초기화</button></div>}
      </div>
      {selected && <article key={selected.id} className={styles.detail} aria-label="선택한 뉴스 해석">
        <button type="button" className={styles.back} onClick={() => { update({ item: "" }, true); requestAnimationFrame(() => document.getElementById(`news-${encodeURIComponent(selected.id)}`)?.focus()); }}>← 뉴스 목록으로</button>
        <div className={styles.detailMeta}><span>{selected.subject}</span><span>{selected.date} · {selected.count}</span></div>
        <h2 ref={heading} tabIndex={-1}>{selected.title}</h2>
        <div className={styles.tags}><span data-risk={selected.kind === "event" && selected.risk}>{selected.direction}</span><span>{selected.quality}</span></div>
        <section className={styles.reading}><h3>저장된 해석</h3><p>{selected.summary ?? "저장된 한국어 요약이 없습니다. 제목에서 투자 논리나 인과관계를 만들어 채우지 않습니다."}</p>
          {selected.reasons.length > 0 && <><h3>연결 근거</h3><ul>{selected.reasons.map((reason, i) => <li key={i}>{reason}</li>)}</ul></>}
          {selected.original !== selected.title && <details><summary>원문 제목</summary><p lang="en">{selected.original}</p></details>}
        </section>
        {selected.headlines.length > 0 && <section className={styles.reading}><h3>묶음을 구성한 뉴스</h3>{selected.headlines.map((event, i) => <article key={i}><small>{event.date} · {event.direction}</small><p>{event.title}</p></article>)}</section>}
        <section className={styles.sources}><div><h3>원천과 대조</h3><span>연결 {selected.sources.length}개</span></div>{selected.sources.map((source, i) => <article key={`${source.id}-${i}`}><span>{String(i + 1).padStart(2, "0")}</span><div><p>{source.title}</p><SourcePeek documentId={source.id} /></div></article>)}{!selected.sources.length && <p>연결된 원천 문서가 제공되지 않았습니다.</p>}</section>
        <section className={styles.audit}><h3>분석 기록과 한계</h3><dl><div><dt>분석 제공자</dt><dd>{selected.provider}</dd></div><div><dt>실행 모델</dt><dd>{selected.model}</dd></div><div><dt>모델 신뢰도</dt><dd>{selected.confidence}</dd></div></dl>{selected.notes.map((note, i) => <p key={i}>{note}</p>)}<p>연결된 자료와 모델 신뢰도는 투자 판단의 검증 완료를 뜻하지 않습니다.</p><Link href="/admin/ai-agents">현재 모델 설정 확인 →</Link></section>
        <nav className={styles.links} aria-label="선택 뉴스 연결">{selected.evidenceHref && <Link prefetch={false} href={selected.evidenceHref as Route}>분석 근거 전체 보기 →</Link>}{selected.symbols.map(symbol => <Link key={symbol} prefetch={false} href={`/stocks/${encodeURIComponent(symbol)}` as Route}>{symbol} 기업 리서치 →</Link>)}</nav>
      </article>}
    </div>
  </section>;
}
