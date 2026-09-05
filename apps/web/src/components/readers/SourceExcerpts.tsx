"use client";
import { usePathname, useSearchParams } from "next/navigation";
import { filterExcerpts, type Excerpt } from "@/lib/research-reader-model";
import styles from "./ResearchReader.module.css";
export function SourceExcerpts({ excerpts }: { excerpts: Excerpt[] | null }) {
  const params = useSearchParams(), path = usePathname(), query = (params.get("q") ?? "").slice(0, 100);
  function update(value: string) {
    const next = new URLSearchParams(window.location.search);
    if (value) next.set("q", value); else next.delete("q");
    window.history.replaceState(null, "", `${path}${next.size ? `?${next}` : ""}${window.location.hash}`);
  }
  if (excerpts === null) return <p className={styles.empty}>발췌 자료를 확인할 수 없습니다.</p>;
  if (!excerpts.length) return <p className={styles.empty}>이 문서에 공개된 발췌가 없습니다.</p>;
  const filtered = filterExcerpts(excerpts, query);
  return <div data-testid="source-excerpts">
    <div className={styles.search}><label>수신된 발췌에서 찾기<input aria-label="발췌 검색" placeholder="구간·위치·내용 검색" value={query} maxLength={100} onChange={e => update(e.target.value)} /></label><button type="button" onClick={() => update("")}>검색 초기화</button></div>
    <p className={styles.caption} role="status">수신 {excerpts.length}개 · 표시 {filtered.length}개</p>
    <p className={styles.caption}>저장된 발췌·요약 필드를 그대로 표시합니다. 완전한 원문이나 검증된 직접 인용으로 간주하지 않습니다.</p>
    {filtered.map(row => <article className={styles.excerpt} key={row.id}>
      <header><span>발췌·요약</span><h3>{row.section}</h3><p>{row.locator}</p></header>
      <p className={styles.original}>{row.summary}</p>
      <details className={styles.details}><summary>발췌 식별자</summary><code>{row.id}</code></details>
    </article>)}
    {!filtered.length && <p className={styles.empty}>검색어와 일치하는 발췌가 없습니다.</p>}
  </div>;
}
